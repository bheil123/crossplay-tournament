"""
DadBot V8 -- MAGPIE-unified tournament bot.

Uses MAGPIE's C engine for ALL move generation + evaluation + simulation.
This eliminates the move generator mismatch that prevented v7 from using
MAGPIE's native multi-threaded simulate() API (28K sims/s).

Architecture:
  - Ignores Python GADDAG move list from tournament runner
  - Calls magpie_simulate() which generates + evaluates all candidates
  - Translates MAGPIE moves to tournament format for the match runner
  - Falls back to Python GADDAG if MAGPIE unavailable

Feature Toggles (env vars):
  BOT_TIER=blitz|fast|standard|deep  (default: fast)
  V8_OPENING_BOOK=0|1     Opening book (default: 1)
  V8_MAX_RESULTS=100       Max candidates from simulate (default: 100)

Performance:
  Snapdragon X Plus: ~28K sims/s (8 threads via MAGPIE BAI)
  i7-8700: ~56K sims/s estimated (2x single-thread, 12 threads)
"""

import os
import sys
import time
import random

from bots.base_engine import BaseEngine

# Add crossplay engine to path
_tourney_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_crossplay_root = os.path.join(os.path.dirname(_tourney_root), 'crossplay')
if os.path.isdir(_crossplay_root) and _crossplay_root not in sys.path:
    sys.path.insert(0, _crossplay_root)


# ---------------------------------------------------------------------------
# Tier config (sim budget)
# ---------------------------------------------------------------------------

# Tier system based on MAGPIE's actual parameters.
# MAGPIE defaults: plies=5, min=500, max=unlimited, GK16@99%.
# We scale down for time-constrained play but keep the architecture.
# GK16 threshold handles stopping automatically — max_iters is a safety cap.
# Tier system: equity-pruned candidates (~40) + GK16 confidence stopping.
# GK16 runs until 99% confident the top move is best.
# max_iters is a time-safety cap; GK16 usually stops earlier.
# min_per_move sets the initial round-robin before BAI focuses.
TIERS = {
    'blitz':    {'PLIES': 2, 'MAX_ITERS': 50000,    'MIN_PER_MOVE': 100},
    'fast':     {'PLIES': 2, 'MAX_ITERS': 200000,   'MIN_PER_MOVE': 250},
    'standard': {'PLIES': 2, 'MAX_ITERS': 1000000,  'MIN_PER_MOVE': 500},
    'deep':     {'PLIES': 2, 'MAX_ITERS': 5000000,  'MIN_PER_MOVE': 500},
}


# ---------------------------------------------------------------------------
# MAGPIE simulate wrapper
# ---------------------------------------------------------------------------

_SIMULATE = None
_SIMULATE_LOADED = False


def _get_simulate():
    global _SIMULATE, _SIMULATE_LOADED
    if _SIMULATE_LOADED:
        return _SIMULATE
    _SIMULATE_LOADED = True
    try:
        from crossplay.magpie_movefinder import simulate, init, is_available
        if init() and is_available():
            _SIMULATE = simulate
            print("  [v8] MAGPIE simulate() loaded (multi-threaded)")
        else:
            print("  [v8] MAGPIE not available, will use Python fallback")
    except Exception as e:
        print(f"  [v8] MAGPIE unavailable: {e}")
    return _SIMULATE


# ---------------------------------------------------------------------------
# Opening book
# ---------------------------------------------------------------------------

_OB_FN = None
_OB_LOADED = False


def _get_opening_move(rack_list):
    global _OB_FN, _OB_LOADED
    if not _OB_LOADED:
        _OB_LOADED = True
        try:
            from crossplay.opening_book import get_opening_move
            _OB_FN = get_opening_move
        except Exception as e:
            print(f"  [v8] Opening book unavailable: {e}")
    if _OB_FN is None:
        return None
    try:
        return _OB_FN(rack_list)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Move format translation
# ---------------------------------------------------------------------------

def _tournament_to_magpie_word(move, board):
    """Add played-through markers to tournament word for MAGPIE.

    Tournament words like 'HELLO' at a position where board already has 'E'
    need to become 'H.LLO' (dot for the played-through E).
    """
    word = move['word']
    row = move['row']
    col = move['col']
    horiz = move['direction'] == 'H'
    tiles_used = move.get('tiles_used', list(word))

    # Track which rack tiles have been consumed
    rack_remaining = list(tiles_used)
    result = []

    for i, ch in enumerate(word):
        r = row - 1 if horiz else row - 1 + i
        c = col - 1 + i if horiz else col - 1
        board_ch = board._grid[r][c] if 0 <= r < 15 and 0 <= c < 15 else None

        if board_ch is not None:
            # Position already has a tile — played through
            result.append('.')
        else:
            # Check if this is a blank
            blanks_used = move.get('blanks_used', [])
            if i in blanks_used:
                result.append(ch.lower())  # lowercase = blank
            else:
                result.append(ch.upper())

    return ''.join(result)


def _magpie_to_tournament_move(sim_result, board, rack):
    """Translate MAGPIE simulate result to tournament move dict.

    MAGPIE uses '.' for played-through tiles and lowercase for blanks.
    Tournament expects clean word + tiles_used (rack tiles only).
    """
    word = sim_result['word']
    row = sim_result['row']
    col = sim_result['col']
    direction = sim_result['direction']
    horiz = direction == 'H'

    tiles_used = []
    blanks_used = []
    clean_word = ''

    for i, ch in enumerate(word):
        if ch == '.':
            # Played-through: get letter from board
            if horiz:
                board_letter = board._grid[row - 1][col - 1 + i]
            else:
                board_letter = board._grid[row - 1 + i][col - 1]
            clean_word += board_letter.upper() if board_letter else ch
        elif ch.islower():
            # Blank tile playing as this letter
            clean_word += ch.upper()
            tiles_used.append('?')
            blanks_used.append(i)
        else:
            clean_word += ch
            tiles_used.append(ch)

    # Compute leave
    rack_list = list(rack.upper())
    for t in tiles_used:
        if t in rack_list:
            rack_list.remove(t)
        elif '?' in rack_list:
            rack_list.remove('?')
    leave = ''.join(rack_list)

    return {
        'word': clean_word,
        'row': row,
        'col': col,
        'direction': direction,
        'score': sim_result['score'],
        'tiles_used': tiles_used,
        'tiles_played': sim_result.get('tiles_played', len(tiles_used)),
        'leave': leave,
        'blanks_used': blanks_used,
        'crosswords': [],
        'equity': sim_result.get('equity', 0.0),
        'num_samples': sim_result.get('num_samples', 0),
    }


# ---------------------------------------------------------------------------
# DadBot V8
# ---------------------------------------------------------------------------

class DadBot(BaseEngine):
    """DadBot V8: MAGPIE-unified bot (28K sims/s)."""

    def __init__(self):
        self._move_times = []
        self._rng = random.Random(42)
        self._flags_printed = False

        tier = os.environ.get('BOT_TIER', 'fast').strip()
        self.config = TIERS.get(tier, TIERS['fast'])
        self.tier = tier

    @property
    def name(self):
        return "DadBot-v8"

    def pick_move(self, board, rack, moves, game_info):
        if not moves:
            return None

        t_start = time.perf_counter()

        if not self._flags_printed:
            self._flags_printed = True
            print(f"  [v8] Tier: {self.tier}, max_iters={self.config['MAX_ITERS']}", flush=True)

        bag_tiles = game_info.get('tiles_in_bag', 1)
        blanks_on_board = game_info.get('blanks_on_board', [])

        # Opening book
        use_ob = os.environ.get('V8_OPENING_BOOK', '1').strip() != '0'
        if use_ob:
            is_empty = all(board._grid[r][c] is None
                          for r in range(15) for c in range(15))
            if is_empty:
                ob = _get_opening_move(list(rack))
                if ob:
                    for m in moves:
                        if (m['word'] == ob['word'] and m['row'] == ob['row']
                                and m['col'] == ob['col']):
                            self._record_time(t_start)
                            return m

        # Near-endgame/endgame: skip simulation (win_pct crashes with few unseen tiles)
        if bag_tiles <= 8:
            best = sorted(moves, key=lambda m: -m['score'])[0]
            self._record_time(t_start)
            return best

        # V8 approach: use MAGPIE for EVERYTHING (move gen + sim).
        # Ignore Python GADDAG moves entirely. Generate our own via MAGPIE,
        # then evaluate with MAGPIE's native multi-threaded simulator.
        # This guarantees zero mismatch between moves and simulation.
        sim_fn = _get_simulate()
        if sim_fn is not None:
            seed = self._rng.randint(1, 2**31 - 1)
            sim_results = sim_fn(
                board, rack,
                num_plies=self.config['PLIES'],
                num_threads=0,
                max_iterations=self.config['MAX_ITERS'],
                min_per_move=self.config['MIN_PER_MOVE'],
                seed=seed,
                board_blanks=blanks_on_board,
                max_results=100,
            )

            if sim_results and len(sim_results) > 0:
                best = _magpie_to_tournament_move(sim_results[0], board, rack)
                self._record_time(t_start)
                return best

        # Fallback: pick highest-scoring Python move
        best = sorted(moves, key=lambda m: -m['score'])[0]
        self._record_time(t_start)
        return best

    def _record_time(self, t_start):
        self._move_times.append(time.perf_counter() - t_start)

    def get_timing_stats(self):
        if not self._move_times:
            return {}
        times = self._move_times
        return {
            'moves': len(times),
            'total_ms': sum(times) * 1000,
            'avg_ms': sum(times) / len(times) * 1000,
            'min_ms': min(times) * 1000,
            'max_ms': max(times) * 1000,
        }

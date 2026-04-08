"""
DadBot V7 -- C-level MC eval + MAGPIE gen_6 leaves + opening book.

Architecture: V7 does MC evaluation in the MAIN PROCESS using
magpie_mc_eval() (single C call per candidate, 75K sims/s).
No worker pool needed for mid-game MC. Endgame/near-endgame
delegated to V5 via super().pick_move() (uses _get_leave_fn hook).

Differences from V5:
- MAGPIE gen_6 leave values (C KLV, 0.7us/call)
- Opening book (2.9M entries, move 1)
- C-level MC eval (162x faster than Python per-sim)
"""

import os
import sys
import time
import random

from bots.dadbot import DadBot as DadBotV5, _leave_value as _v5_leave_value
from bots.dadbot import _ensure_resources, _compute_unseen, _rank_by_equity, RACK_SIZE

# Add crossplay engine to path
_tourney_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_crossplay_root = os.path.join(os.path.dirname(_tourney_root), 'crossplay')
if os.path.isdir(_crossplay_root) and _crossplay_root not in sys.path:
    sys.path.insert(0, _crossplay_root)


# ---------------------------------------------------------------------------
# MAGPIE C leave evaluation
# ---------------------------------------------------------------------------

_MAGPIE_LEAVE = None
_MAGPIE_LEAVE_LOADED = False
_MAGPIE_LEAVE_WARNED = False


def _load_magpie_leave():
    global _MAGPIE_LEAVE, _MAGPIE_LEAVE_LOADED
    if _MAGPIE_LEAVE_LOADED:
        return
    _MAGPIE_LEAVE_LOADED = True
    try:
        from crossplay.magpie_movefinder import leave_value, is_available
        if is_available():
            _MAGPIE_LEAVE = leave_value
            print("  [v7] MAGPIE leave evaluation loaded")
        else:
            print("  [v7] MAGPIE DLL not available, using formula leaves")
    except Exception as e:
        print(f"  [v7] MAGPIE leave unavailable: {e}")


def _v7_leave_value(leave_str, bag_empty=False, bag_tiles=100):
    """Leave evaluation using MAGPIE C KLV (0.7us/call)."""
    global _MAGPIE_LEAVE_WARNED
    _load_magpie_leave()
    if _MAGPIE_LEAVE is not None:
        try:
            return _MAGPIE_LEAVE(leave_str)
        except Exception as e:
            if not _MAGPIE_LEAVE_WARNED:
                _MAGPIE_LEAVE_WARNED = True
                print(f"  [v7] MAGPIE leave call failed (once): {e}")
    return _v5_leave_value(leave_str, bag_empty, bag_tiles)


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
            print(f"  [v7] Opening book unavailable: {e}")
    if _OB_FN is None:
        return None
    try:
        return _OB_FN(rack_list)
    except Exception as e:
        print(f"  [v7] Opening book lookup failed: {e}")
        return None


# ---------------------------------------------------------------------------
# C MC eval wrapper
# ---------------------------------------------------------------------------

_MC_EVAL = None
_MC_EVAL_LOADED = False


def _get_mc_eval():
    global _MC_EVAL, _MC_EVAL_LOADED
    if _MC_EVAL_LOADED:
        return _MC_EVAL
    _MC_EVAL_LOADED = True
    try:
        from crossplay.magpie_movefinder import mc_eval, is_available
        if is_available():
            _MC_EVAL = mc_eval
            print("  [v7] C MC eval loaded")
        else:
            print("  [v7] C MC eval not available, falling back to v5 worker pool")
    except Exception as e:
        print(f"  [v7] C MC eval unavailable: {e}")
    return _MC_EVAL


# ---------------------------------------------------------------------------
# Play-to-completion MC
# ---------------------------------------------------------------------------

def _play_to_completion(board, your_rack, unseen_pool, your_move_score,
                        blanks_on_board, rng, leave_fn=None):
    """Simulate game to completion with greedy play, return final spread.

    After your candidate move (already scored as your_move_score):
    1. Shuffle unseen, deal opponent rack (7 tiles)
    2. Alternate: opponent plays best, you play best
    3. Crossplay endgame: both get final turn after bag empties
    4. Return your_total - opp_total (including your_move_score)

    Uses Cython find_best_score_c for speed (~0.5ms per move generation).
    """
    from engine.board import Board as EngBoard
    from engine.config import VALID_TWO_LETTER, BINGO_BONUS, RACK_SIZE

    if not _ensure_ptc_accel():
        return None
    accel = _get_accel()
    if accel is None or _w_gdata_bytes is None:
        return None

    # Copy board state
    sim_board = board.copy() if hasattr(board, 'copy') else EngBoard()
    if not hasattr(board, 'copy'):
        for r in range(15):
            for c in range(15):
                if board._grid[r][c] is not None:
                    sim_board._grid[r][c] = board._grid[r][c]

    # Build blank set (0-indexed)
    bb_set = set()
    for entry in (blanks_on_board or []):
        if len(entry) >= 2:
            bb_set.add((entry[0] - 1, entry[1] - 1))

    # Shuffle unseen and deal
    pool = list(unseen_pool)
    rng.shuffle(pool)

    opp_rack_list = pool[:min(RACK_SIZE, len(pool))]
    remaining_pool = pool[min(RACK_SIZE, len(pool)):]

    your_total = your_move_score
    opp_total = 0
    bag = list(remaining_pool)
    final_turns = None  # None = mid-game, 2/1/0 = final turns

    # Racks as strings
    opp_rack = ''.join(opp_rack_list)
    # Your rack is whatever leave you have (tiles_used already removed by caller)
    # We need your leave -- the caller should pass it
    # For now, draw from bag to fill your rack
    your_rack_list = list(your_rack)
    while len(your_rack_list) < RACK_SIZE and bag:
        your_rack_list.append(bag.pop())
    your_rack_str = ''.join(your_rack_list)

    # Simulate alternating turns (opponent first after your move)
    for turn in range(30):  # safety cap
        if final_turns is not None and final_turns <= 0:
            break

        # Whose turn?
        is_opp_turn = (turn % 2 == 0)  # opponent goes first after your move
        rack_str = opp_rack if is_opp_turn else your_rack_str

        if not rack_str:
            if final_turns is not None:
                final_turns -= 1
            continue

        # Build context and find best move
        ctx = _w_accel.prepare_board_context(
            sim_board._grid, _w_gdata_bytes, bb_set,
            _w_word_set, VALID_TWO_LETTER,
            _TV, _BONUS, BINGO_BONUS, RACK_SIZE,
        ) if _w_accel else None

        if ctx is None:
            break

        score, word, row, col, dir_str = _w_accel.find_best_score_c(ctx, rack_str)

        if score <= 0 or word is None:
            # Pass
            if final_turns is not None:
                final_turns -= 1
            continue

        if final_turns is not None:
            final_turns -= 1

        # Place move
        horiz = dir_str == 'H'
        placed = sim_board.place_move(word, row, col, horiz)

        # Update score
        if is_opp_turn:
            opp_total += score
        else:
            your_total += score

        # Update rack: remove used tiles, draw new
        rack_list = list(rack_str)
        for i, letter in enumerate(word):
            r = row if horiz else row + i
            c = col + i if horiz else col
            if (r, c) in {pos for pos in placed}:
                # This position was newly placed -- consumed from rack
                if letter in rack_list:
                    rack_list.remove(letter)
                elif '?' in rack_list:
                    rack_list.remove('?')

        # Draw from bag
        while len(rack_list) < RACK_SIZE and bag:
            rack_list.append(bag.pop())

        # Check if bag just emptied
        if len(bag) == 0 and final_turns is None:
            final_turns = 2

        new_rack = ''.join(rack_list)
        if is_opp_turn:
            opp_rack = new_rack
        else:
            your_rack_str = new_rack

    return your_total - opp_total


def _ptc_eval_candidate(board, move, unseen_pool, blanks_on_board,
                        leave_str, rng, k_sims=20, leave_fn=None):
    """Evaluate one candidate via play-to-completion MC.

    Returns average final spread across k_sims simulations.
    """
    from engine.board import Board as EngBoard

    # Place candidate move on a copy
    eval_board = board.copy() if hasattr(board, 'copy') else EngBoard()
    if not hasattr(board, 'copy'):
        for r in range(15):
            for c in range(15):
                if board._grid[r][c] is not None:
                    eval_board._grid[r][c] = board._grid[r][c]

    horizontal = move['direction'] == 'H'
    placed = eval_board.place_move(move['word'], move['row'], move['col'], horizontal)

    # Build post-move blanks
    move_blanks = list(blanks_on_board)
    for bi in move.get('blanks_used', []):
        if horizontal:
            move_blanks.append((move['row'], move['col'] + bi, move['word'][bi]))
        else:
            move_blanks.append((move['row'] + bi, move['col'], move['word'][bi]))

    total_spread = 0.0
    n = 0

    for _ in range(k_sims):
        spread = _play_to_completion(
            eval_board, leave_str, unseen_pool, move['score'],
            move_blanks, rng, leave_fn=leave_fn)
        if spread is not None:
            total_spread += spread
            n += 1

    eval_board.undo_move(placed)

    return total_spread / n if n > 0 else None


# ---------------------------------------------------------------------------
# Accel helpers for play-to-completion (worker-level access in main process)
# ---------------------------------------------------------------------------
_w_accel = None
_w_gdata_bytes = None
_w_word_set = None
_TV = None
_BONUS = None


def _ensure_ptc_accel():
    """Load Cython accel for play-to-completion in main process."""
    global _w_accel, _w_gdata_bytes, _w_word_set, _TV, _BONUS
    if _w_accel is not None:
        return True
    _ensure_resources()
    try:
        import gaddag_accel
        _w_accel = gaddag_accel
    except ImportError:
        try:
            sys.path.insert(0, _crossplay_root)
            import gaddag_accel
            _w_accel = gaddag_accel
        except ImportError:
            return False
    from engine.config import TILE_VALUES, BONUS_SQUARES
    from engine.gaddag import get_gaddag
    from engine.dictionary import get_dictionary
    _w_gdata_bytes = bytes(get_gaddag()._data)
    _w_word_set = get_dictionary()._words

    _TV_local = [0] * 26
    for ch, val in TILE_VALUES.items():
        if ch != '?':
            _TV_local[ord(ch) - 65] = val
    _TV = _TV_local

    _BONUS_local = [[(1, 1)] * 15 for _ in range(15)]
    for (r1, c1), btype in BONUS_SQUARES.items():
        r0, c0 = r1 - 1, c1 - 1
        if btype == '2L': _BONUS_local[r0][c0] = (2, 1)
        elif btype == '3L': _BONUS_local[r0][c0] = (3, 1)
        elif btype == '2W': _BONUS_local[r0][c0] = (1, 2)
        elif btype == '3W': _BONUS_local[r0][c0] = (1, 3)
    _BONUS = _BONUS_local

    return True


def _get_accel():
    """Get Cython accel module."""
    return _w_accel


# ---------------------------------------------------------------------------
# DadBot V7
# ---------------------------------------------------------------------------

class DadBot(DadBotV5):
    """DadBot V7: C MC eval + MAGPIE leaves + opening book + Bogowin."""

    def __init__(self):
        super().__init__()
        _load_magpie_leave()
        self._move_times = []
        self._rng = random.Random(42)
        self._bogowin = None
        self._bogowin_loaded = False

    @property
    def name(self):
        return "DadBot-v7"

    def _get_leave_fn(self):
        """Override: use MAGPIE gen_6 C KLV leaves."""
        return _v7_leave_value

    def _get_bogowin(self):
        """Lazy-load Bogowin win% lookup."""
        if not self._bogowin_loaded:
            self._bogowin_loaded = True
            if not os.environ.get('V7_BOGOWIN'):
                return self._bogowin  # disabled by default; enable with V7_BOGOWIN=1
            try:
                from crossplay.bogowin import get_win_probability
                # Verify it works
                test = get_win_probability(0, 50)
                if isinstance(test, (int, float)):
                    self._bogowin = get_win_probability
                    print("  [v7] Bogowin win% loaded")
            except Exception as e:
                print(f"  [v7] Bogowin unavailable: {e}")
        return self._bogowin

    def pick_move(self, board, rack, moves, game_info):
        if not moves:
            return None

        t_start = time.perf_counter()
        _ensure_resources()

        bag_tiles = game_info.get('tiles_in_bag', 1)
        blanks_on_board = game_info.get('blanks_on_board', [])
        grid = [row[:] for row in board._grid]
        cfg = self.config

        # -----------------------------------------------------------
        # Opening book: first move on empty board
        # -----------------------------------------------------------
        is_empty = all(grid[r][c] is None for r in range(15) for c in range(15))
        if is_empty:
            ob = _get_opening_move(list(rack))
            if ob:
                for m in moves:
                    if m['word'] == ob['word'] and m['row'] == ob['row'] and m['col'] == ob['col']:
                        self._record_time(t_start)
                        return m

        # -----------------------------------------------------------
        # Endgame / near-endgame / no C MC: delegate to v5
        # (v5 calls self._get_leave_fn() which returns MAGPIE leaves)
        # -----------------------------------------------------------
        mc_eval_fn = _get_mc_eval()
        if bag_tiles <= 8 or mc_eval_fn is None or cfg['K_SIMS'] <= 0:
            result = super().pick_move(board, rack, moves, game_info)
            self._record_time(t_start)
            return result

        # -----------------------------------------------------------
        # Mid-game: C MC eval or play-to-completion
        # -----------------------------------------------------------

        # 1-ply ranking with MAGPIE leaves
        leave_fn = self._get_leave_fn()
        bag_empty = bag_tiles <= RACK_SIZE
        ranked = _rank_by_equity(moves, bag_tiles, leave_fn=leave_fn)

        n_cands = cfg['N_CANDIDATES']
        candidates = ranked[:n_cands]

        # Build unseen pool
        unseen_pool = _compute_unseen(grid, rack, blanks_on_board)
        unseen_str = ''.join(unseen_pool)

        if not unseen_str:
            self._record_time(t_start)
            return candidates[0][0]

        k_sims = cfg['K_SIMS']
        current_spread = game_info.get('your_score', 0) - game_info.get('opp_score', 0)

        # Load Bogowin for win% selection
        bogowin_fn = self._get_bogowin()

        # Play-to-completion mode (V7_PTC env var) -- uses C bridge
        use_ptc = bool(os.environ.get('V7_PTC'))
        ptc_fn = None
        if use_ptc:
            try:
                from crossplay.magpie_movefinder import play_to_completion, is_available
                if is_available():
                    ptc_fn = play_to_completion
            except Exception:
                pass

        best_move = candidates[0][0]
        best_metric = float('-inf')

        if ptc_fn is not None:
            # Hybrid: 2-ply MC first for all candidates, then PTC for top 3
            # Step 1: 2-ply MC to rank all candidates
            mc_results = []
            eval_board = board.copy() if hasattr(board, 'copy') else self._copy_board(board)

            for move, equity_1ply, leave_val in candidates:
                horizontal = move['direction'] == 'H'
                placed = eval_board.place_move(move['word'], move['row'], move['col'], horizontal)

                move_blanks = list(blanks_on_board)
                for bi in move.get('blanks_used', []):
                    if horizontal:
                        move_blanks.append((move['row'], move['col'] + bi, move['word'][bi]))
                    else:
                        move_blanks.append((move['row'] + bi, move['col'], move['word'][bi]))

                seed = self._rng.randint(1, 2**31 - 1)
                result = mc_eval_fn(eval_board, '', unseen_str, k_sims=k_sims, seed=seed,
                                    board_blanks=move_blanks)
                eval_board.undo_move(placed)

                if result and result.get('n_sims', 0) > 0:
                    mc_eq = move['score'] - result['avg_opp'] + leave_val
                else:
                    mc_eq = equity_1ply
                mc_results.append((move, mc_eq, leave_val, move_blanks))

            # Step 2: PTC refinement for top 3 by MC equity
            mc_results.sort(key=lambda x: -x[1])
            ptc_k = 75  # 75 full games per finalist (~0.8s each, SE ~12pts)
            ptc_top = min(3, len(mc_results))

            for move, mc_eq, leave_val, move_blanks in mc_results[:ptc_top]:
                horizontal = move['direction'] == 'H'
                placed = eval_board.place_move(move['word'], move['row'], move['col'], horizontal)

                leave_str = move.get('leave', '')
                seed = self._rng.randint(1, 2**31 - 1)
                ptc_result = ptc_fn(eval_board, leave_str, unseen_str,
                                    move['score'], k_sims=ptc_k, seed=seed,
                                    board_blanks=move_blanks)
                eval_board.undo_move(placed)

                if ptc_result and ptc_result.get('n_sims', 0) > 0:
                    avg_spread = ptc_result['avg_spread']
                    if bogowin_fn is not None:
                        tiles_used = move.get('tiles_used', list(move['word']))
                        bag_after = max(0, bag_tiles - len(tiles_used))
                        projected_spread = current_spread + avg_spread
                        metric = bogowin_fn(int(projected_spread), bag_after)
                    else:
                        metric = avg_spread
                else:
                    metric = mc_eq

                if metric > best_metric:
                    best_metric = metric
                    best_move = move
        else:
            # Standard 2-ply C MC eval
            eval_board = board.copy() if hasattr(board, 'copy') else self._copy_board(board)

            for move, equity_1ply, leave_val in candidates:
                horizontal = move['direction'] == 'H'
                placed = eval_board.place_move(move['word'], move['row'], move['col'], horizontal)

                move_blanks = list(blanks_on_board)
                for bi in move.get('blanks_used', []):
                    if horizontal:
                        move_blanks.append((move['row'], move['col'] + bi, move['word'][bi]))
                    else:
                        move_blanks.append((move['row'] + bi, move['col'], move['word'][bi]))

                seed = self._rng.randint(1, 2**31 - 1)
                result = mc_eval_fn(eval_board, '', unseen_str, k_sims=k_sims, seed=seed,
                                    board_blanks=move_blanks)

                eval_board.undo_move(placed)

                if result and result.get('n_sims', 0) > 0:
                    mc_eq = move['score'] - result['avg_opp'] + leave_val
                else:
                    mc_eq = equity_1ply

                if bogowin_fn is not None:
                    tiles_used = move.get('tiles_used', list(move['word']))
                    bag_after = max(0, bag_tiles - len(tiles_used))
                    projected_spread = current_spread + mc_eq
                    metric = bogowin_fn(int(projected_spread), bag_after)
                else:
                    metric = mc_eq

                if metric > best_metric:
                    best_metric = metric
                    best_move = move

        self._record_time(t_start)
        return best_move

    @staticmethod
    def _copy_board(board):
        """Fallback board copy if board.copy() doesn't exist."""
        from engine.board import Board as EngBoard
        b = EngBoard()
        for r in range(15):
            for c in range(15):
                if board._grid[r][c] is not None:
                    b._grid[r][c] = board._grid[r][c]
        return b

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

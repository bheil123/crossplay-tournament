"""
DadBot V7 -- C-level MC eval + MAGPIE leaves + opening book + feature toggles.

Architecture: V7 does MC evaluation in the MAIN PROCESS using
magpie_mc_eval() (single C call per candidate, ~1K sims/s on ARM64,
~2K sims/s on i7-8700). All features are independently toggleable
via environment variables for A/B testing.

Feature Toggles (env vars):
  V7_OPENING_BOOK=0|1     Opening book on/off (default: 1=on)
  V7_LEAVES=magpie|formula|superleaves  Leave source (default: magpie)
  V7_MC=c|python           MC engine: C bridge or v5 Python workers (default: c)
  V7_BOGOWIN=0|1           Bogowin win% metric (default: 0=off)
  V7_BOGOWIN_BLEND=0.0-1.0 Blend: 0=pure win%, 1=pure equity (default: 1.0)
  V7_PTC=0|1               Play-to-completion mode (default: 0=off)
  V7_NEAR_ENDGAME=0|1      V7 near-endgame evaluator (default: 0=delegate to v5)
  V7_TILE_TRACKER=0|1      Precise unseen tile tracking (default: 0=off)
  V7_NE_BAG=1-8            Bag threshold for near-endgame (default: 8)

Inherited from V5:
  BOT_TIER=blitz|fast|standard|deep  (default: fast)
  MC_WORKERS=N             Worker count override
  DADBOT_N=N               Override N_CANDIDATES
  DADBOT_K=N               Override K_SIMS
  DADBOT_TIMING=1          Timing diagnostics

Tier config (only N_CANDIDATES and K_SIMS used by V7):
  blitz:    ~1s/move   (N=7,  K=150)
  fast:     ~3s/move   (N=15, K=400)   [default]
  standard: ~10s/move  (N=30, K=1500)
  deep:     ~30s/move  (N=35, K=2000)
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
# Feature flag helpers
# ---------------------------------------------------------------------------

def _flag(name, default=''):
    """Get env var, strip whitespace."""
    return os.environ.get(name, default).strip()


def _flag_bool(name, default=False):
    """Get boolean env var. '0'/'false'/''=False, anything else=True."""
    val = _flag(name)
    if not val:
        return default
    return val not in ('0', 'false', 'no', 'off')


def _flag_float(name, default=1.0):
    """Get float env var."""
    val = _flag(name)
    if not val:
        return default
    try:
        return float(val)
    except ValueError:
        return default


# ---------------------------------------------------------------------------
# Leave evaluation — toggleable source
# ---------------------------------------------------------------------------

_MAGPIE_LEAVE = None
_MAGPIE_LEAVE_LOADED = False
_MAGPIE_LEAVE_WARNED = False
_SUPERLEAVES_TABLE = None
_SUPERLEAVES_LOADED = False


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


def _load_superleaves():
    global _SUPERLEAVES_TABLE, _SUPERLEAVES_LOADED
    if _SUPERLEAVES_LOADED:
        return
    _SUPERLEAVES_LOADED = True
    try:
        import pickle
        sl_path = os.path.join(_tourney_root, 'engine', 'data', 'deployed_leaves.pkl')
        with open(sl_path, 'rb') as f:
            data = pickle.load(f)
        if isinstance(data, dict) and 'table' in data:
            _SUPERLEAVES_TABLE = data['table']
        else:
            _SUPERLEAVES_TABLE = data
        print(f"  [v7] SuperLeaves table loaded ({len(_SUPERLEAVES_TABLE):,} entries)")
    except Exception as e:
        print(f"  [v7] SuperLeaves unavailable: {e}")


def _formula_leave_value(leave_str, bag_empty=False, bag_tiles=100):
    """V5's hand-tuned per-tile formula."""
    return _v5_leave_value(leave_str, bag_empty, bag_tiles)


def _superleaves_leave_value(leave_str, bag_empty=False, bag_tiles=100):
    """Trained SuperLeaves table lookup."""
    _load_superleaves()
    if _SUPERLEAVES_TABLE is not None:
        key = tuple(sorted(leave_str.upper()))
        return _SUPERLEAVES_TABLE.get(key, 0.0)
    return _formula_leave_value(leave_str, bag_empty, bag_tiles)


def _magpie_leave_value(leave_str, bag_empty=False, bag_tiles=100):
    """MAGPIE C KLV leave lookup (0.7us/call)."""
    global _MAGPIE_LEAVE_WARNED
    _load_magpie_leave()
    if _MAGPIE_LEAVE is not None:
        try:
            return _MAGPIE_LEAVE(leave_str)
        except Exception as e:
            if not _MAGPIE_LEAVE_WARNED:
                _MAGPIE_LEAVE_WARNED = True
                print(f"  [v7] MAGPIE leave call failed (once): {e}")
    return _formula_leave_value(leave_str, bag_empty, bag_tiles)


def _get_leave_fn_by_mode(mode):
    """Return leave function based on V7_LEAVES mode."""
    if mode == 'formula':
        return _formula_leave_value
    elif mode == 'superleaves':
        return _superleaves_leave_value
    else:  # 'magpie' (default)
        return _magpie_leave_value


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
# Play-to-completion MC (unchanged from original)
# ---------------------------------------------------------------------------

def _play_to_completion(board, your_rack, unseen_pool, your_move_score,
                        blanks_on_board, rng, leave_fn=None):
    """Simulate game to completion with greedy play, return final spread."""
    from engine.board import Board as EngBoard
    from engine.config import VALID_TWO_LETTER, BINGO_BONUS, RACK_SIZE

    if not _ensure_ptc_accel():
        return None
    accel = _get_accel()
    if accel is None or _w_gdata_bytes is None:
        return None

    sim_board = board.copy() if hasattr(board, 'copy') else EngBoard()
    if not hasattr(board, 'copy'):
        for r in range(15):
            for c in range(15):
                if board._grid[r][c] is not None:
                    sim_board._grid[r][c] = board._grid[r][c]

    bb_set = set()
    for entry in (blanks_on_board or []):
        if len(entry) >= 2:
            bb_set.add((entry[0] - 1, entry[1] - 1))

    pool = list(unseen_pool)
    rng.shuffle(pool)

    opp_rack_list = pool[:min(RACK_SIZE, len(pool))]
    remaining_pool = pool[min(RACK_SIZE, len(pool)):]

    your_total = your_move_score
    opp_total = 0
    bag = list(remaining_pool)
    final_turns = None

    opp_rack = ''.join(opp_rack_list)
    your_rack_list = list(your_rack)
    while len(your_rack_list) < RACK_SIZE and bag:
        your_rack_list.append(bag.pop())
    your_rack_str = ''.join(your_rack_list)

    for turn in range(30):
        if final_turns is not None and final_turns <= 0:
            break

        is_opp_turn = (turn % 2 == 0)
        rack_str = opp_rack if is_opp_turn else your_rack_str

        if not rack_str:
            if final_turns is not None:
                final_turns -= 1
            continue

        ctx = _w_accel.prepare_board_context(
            sim_board._grid, _w_gdata_bytes, bb_set,
            _w_word_set, VALID_TWO_LETTER,
            _TV, _BONUS, BINGO_BONUS, RACK_SIZE,
        ) if _w_accel else None

        if ctx is None:
            break

        score, word, row, col, dir_str = _w_accel.find_best_score_c(ctx, rack_str)

        if score <= 0 or word is None:
            if final_turns is not None:
                final_turns -= 1
            continue

        if final_turns is not None:
            final_turns -= 1

        horiz = dir_str == 'H'
        placed = sim_board.place_move(word, row, col, horiz)

        if is_opp_turn:
            opp_total += score
        else:
            your_total += score

        rack_list = list(rack_str)
        for i, letter in enumerate(word):
            r = row if horiz else row + i
            c = col + i if horiz else col
            if (r, c) in {pos for pos in placed}:
                if letter in rack_list:
                    rack_list.remove(letter)
                elif '?' in rack_list:
                    rack_list.remove('?')

        while len(rack_list) < RACK_SIZE and bag:
            rack_list.append(bag.pop())

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
    """Evaluate one candidate via play-to-completion MC."""
    from engine.board import Board as EngBoard

    eval_board = board.copy() if hasattr(board, 'copy') else EngBoard()
    if not hasattr(board, 'copy'):
        for r in range(15):
            for c in range(15):
                if board._grid[r][c] is not None:
                    eval_board._grid[r][c] = board._grid[r][c]

    horizontal = move['direction'] == 'H'
    placed = eval_board.place_move(move['word'], move['row'], move['col'], horizontal)

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
# Accel helpers (shared by PTC, near-endgame, and main process Cython)
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


# Near-endgame time budgets per tier
_V7_NE_TIMES = {'blitz': 2.0, 'fast': 5.0, 'standard': 15.0, 'deep': 30.0}


# ---------------------------------------------------------------------------
# DadBot V7
# ---------------------------------------------------------------------------

class DadBot(DadBotV5):
    """DadBot V7: C MC eval + toggleable features for A/B testing."""

    def __init__(self):
        super().__init__()
        self._move_times = []
        self._rng = random.Random(42)
        self._bogowin = None
        self._bogowin_loaded = False
        self._flags_printed = False

    @property
    def name(self):
        return "DadBot-v7"

    def _print_flags(self):
        """Print active feature flags once."""
        if self._flags_printed:
            return
        self._flags_printed = True
        flags = []
        if _flag('V7_LEAVES', 'magpie') != 'magpie':
            flags.append(f"leaves={_flag('V7_LEAVES')}")
        if not _flag_bool('V7_OPENING_BOOK', True):
            flags.append("ob=off")
        if _flag('V7_MC', 'c') != 'c':
            flags.append(f"mc={_flag('V7_MC')}")
        if _flag_bool('V7_BOGOWIN'):
            blend = _flag_float('V7_BOGOWIN_BLEND', 1.0)
            flags.append(f"bogowin(blend={blend})")
        if _flag_bool('V7_PTC'):
            flags.append("ptc")
        if _flag_bool('V7_NEAR_ENDGAME'):
            flags.append(f"ne(bag<={_flag('V7_NE_BAG', '8')})")
        if _flag_bool('V7_TILE_TRACKER'):
            flags.append("tt")
        if flags:
            print(f"  [v7] Flags: {', '.join(flags)}", flush=True)

    def _get_leave_fn(self):
        """Override: use configured leave source."""
        mode = _flag('V7_LEAVES', 'magpie')
        return _get_leave_fn_by_mode(mode)

    def _get_bogowin(self):
        """Lazy-load Bogowin win% lookup."""
        if not self._bogowin_loaded:
            self._bogowin_loaded = True
            if not _flag_bool('V7_BOGOWIN'):
                return self._bogowin
            try:
                from crossplay.bogowin import get_win_probability
                test = get_win_probability(0, 50)
                if isinstance(test, (int, float)):
                    self._bogowin = get_win_probability
                    print("  [v7] Bogowin win% loaded")
            except Exception as e:
                print(f"  [v7] Bogowin unavailable: {e}")
        return self._bogowin

    def _bogowin_metric(self, equity, current_spread, bag_after):
        """Compute blended equity/win% metric."""
        alpha = _flag_float('V7_BOGOWIN_BLEND', 1.0)
        if alpha >= 1.0:
            return equity  # pure equity (default)

        bogowin_fn = self._get_bogowin()
        if bogowin_fn is None:
            return equity

        projected_spread = current_spread + equity
        win_pct = bogowin_fn(int(projected_spread), bag_after)
        scale = 400.0  # map win% [0-1] to equity-comparable range

        if alpha <= 0.0:
            return win_pct * scale  # pure win%

        return alpha * equity + (1 - alpha) * win_pct * scale

    def pick_move(self, board, rack, moves, game_info):
        if not moves:
            return None

        t_start = time.perf_counter()
        _ensure_resources()
        self._print_flags()

        bag_tiles = game_info.get('tiles_in_bag', 1)
        blanks_on_board = game_info.get('blanks_on_board', [])
        grid = [row[:] for row in board._grid]
        cfg = self.config

        # -----------------------------------------------------------
        # Opening book (V7_OPENING_BOOK, default: on)
        # -----------------------------------------------------------
        if _flag_bool('V7_OPENING_BOOK', True):
            is_empty = all(grid[r][c] is None for r in range(15) for c in range(15))
            if is_empty:
                ob = _get_opening_move(list(rack))
                if ob:
                    for m in moves:
                        if m['word'] == ob['word'] and m['row'] == ob['row'] and m['col'] == ob['col']:
                            self._record_time(t_start)
                            return m

        # -----------------------------------------------------------
        # Near-endgame / endgame routing
        # -----------------------------------------------------------
        ne_bag_threshold = int(_flag('V7_NE_BAG', '8'))
        use_c_mc = _flag('V7_MC', 'c') == 'c'

        if bag_tiles <= ne_bag_threshold:
            if _flag_bool('V7_NEAR_ENDGAME'):
                # V7's own near-endgame: uses v5's multiprocessing with
                # ARM64 Cython workers (no timeout issues)
                result = self._near_endgame_pick(board, rack, moves, game_info)
                self._record_time(t_start)
                return result
            else:
                # Delegate to V5 (original behavior)
                result = super().pick_move(board, rack, moves, game_info)
                self._record_time(t_start)
                return result

        # -----------------------------------------------------------
        # MC engine selection (V7_MC, default: c)
        # -----------------------------------------------------------
        if use_c_mc:
            mc_eval_fn = _get_mc_eval()
        else:
            mc_eval_fn = None  # forces v5 Python MC path

        if mc_eval_fn is None or cfg['K_SIMS'] <= 0:
            # No C MC available or disabled — delegate to v5
            result = super().pick_move(board, rack, moves, game_info)
            self._record_time(t_start)
            return result

        # -----------------------------------------------------------
        # Mid-game: C MC eval (or PTC)
        # -----------------------------------------------------------
        leave_fn = self._get_leave_fn()
        ranked = _rank_by_equity(moves, bag_tiles, leave_fn=leave_fn)

        n_cands = cfg['N_CANDIDATES']
        candidates = ranked[:n_cands]

        unseen_pool = _compute_unseen(grid, rack, blanks_on_board)
        unseen_str = ''.join(unseen_pool)

        if not unseen_str:
            self._record_time(t_start)
            return candidates[0][0]

        k_sims = cfg['K_SIMS']
        current_spread = game_info.get('your_score', 0) - game_info.get('opp_score', 0)
        bogowin_fn = self._get_bogowin()

        # PTC mode
        use_ptc = _flag_bool('V7_PTC')
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
            # PTC hybrid path (unchanged)
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

            mc_results.sort(key=lambda x: -x[1])
            ptc_k = 75
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
                    tiles_used = move.get('tiles_used', list(move['word']))
                    bag_after = max(0, bag_tiles - len(tiles_used))
                    metric = self._bogowin_metric(avg_spread, current_spread, bag_after)
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

                tiles_used = move.get('tiles_used', list(move['word']))
                bag_after = max(0, bag_tiles - len(tiles_used))
                metric = self._bogowin_metric(mc_eq, current_spread, bag_after)

                if metric > best_metric:
                    best_metric = metric
                    best_move = move

        self._record_time(t_start)
        return best_move

    def _near_endgame_pick(self, board, rack, moves, game_info):
        """V7 near-endgame handler: reuses v5's multiprocessing with
        ARM64 Cython workers. Adds tile tracking and Bogowin integration."""
        from bots.near_endgame import evaluate_near_endgame

        bag_tiles = game_info.get('tiles_in_bag', 1)
        blanks_on_board = game_info.get('blanks_on_board', [])
        grid = [row[:] for row in board._grid]

        unseen_pool = _compute_unseen(grid, rack, blanks_on_board)

        # Tile tracker for precise unseen counts
        tile_counts = None
        if _flag_bool('V7_TILE_TRACKER'):
            from collections import Counter
            tile_counts = Counter(unseen_pool)

        # Time budget from tier
        tier = _flag('BOT_TIER', 'fast')
        time_budget = _V7_NE_TIMES.get(tier, 5.0)

        leave_fn = self._get_leave_fn()
        current_spread = game_info.get('your_score', 0) - game_info.get('opp_score', 0)

        try:
            result = evaluate_near_endgame(
                board=board,
                rack=rack,
                moves=moves,
                unseen_pool=unseen_pool,
                blanks_on_board=blanks_on_board,
                bag_size=bag_tiles,
                time_budget=time_budget,
                leave_fn=leave_fn,
                tile_counts=tile_counts,
                current_spread=current_spread,
                bogowin_fn=self._get_bogowin() if _flag_bool('V7_BOGOWIN') else None,
                bogowin_blend=_flag_float('V7_BOGOWIN_BLEND', 1.0),
            )
            if result is not None:
                return result
        except Exception as e:
            print(f"  [v7] Near-endgame error: {e}", flush=True)

        # Fallback to v5
        return super().pick_move(board, rack, moves, game_info)

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

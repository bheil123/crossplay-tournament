"""
DadBot v5 -- Parallel Cython-accelerated Monte Carlo 2-ply evaluation
with performance tiers.

Uses the crossplay engine's compiled C extension (gaddag_accel.pyd) for
blazing-fast opponent simulation with multiprocessing parallelism.

Architecture:
  - Persistent worker pool initialized on first pick_move()
  - Each worker loads GADDAG + dictionary once (30MB, cached in process)
  - Per-move: serialize grid + blank set, fan out candidates to workers
  - Each worker: reconstruct board, place candidate, create BoardContext,
    run K MC sims with early stopping, return avg_opp
  - Main process: aggregate results, add leave value, pick best

Evaluation modes:
  - Mid-game (bag > 8): Parallel MC 2-ply + leave formula
  - Near-endgame (bag 1-8): Hybrid -- exhaustive 3-ply for bag-emptying
    moves, parity-adjusted 1-ply for non-emptying moves
  - Endgame (bag=0): Deterministic minimax (opponent rack known exactly)

Performance tiers (BOT_TIER env var):
  - blitz:    ~1s/move   (N=7,  K=150,  SE=1.5, min_sims=20)
  - fast:     ~3s/move   (N=15, K=400,  SE=1.2, min_sims=50)  [default]
  - standard: ~10s/move  (N=30, K=1500, SE=0.8, min_sims=80)
  - deep:     ~30s/move  (N=35, K=2000, SE=0.5, min_sims=100)

Falls back to sequential Python if Cython extension is unavailable.
"""

import os
import sys
import random
import time
from itertools import combinations
from concurrent.futures import ProcessPoolExecutor

from bots.base_engine import BaseEngine, get_legal_moves

# Private RNG for DadBot internals (MC seeds, exchange sampling).
# CRITICAL: using the global random module would contaminate the game's tile
# draw sequence, making outcomes depend on N_CANDIDATES and K_SIMS rather than
# just the game seed. This private instance isolates DadBot's randomness.
_rng = random.Random(42)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_CROSSPLAY_DIR = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'crossplay',
))
_TOURNAMENT_DIR = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..',
))

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
sys.path.insert(0, _TOURNAMENT_DIR)
from engine.config import (
    TILE_VALUES, TILE_DISTRIBUTION, BONUS_SQUARES,
    VALID_TWO_LETTER, BINGO_BONUS, RACK_SIZE, BOARD_SIZE,
)

# ---------------------------------------------------------------------------
# Performance tier system
# ---------------------------------------------------------------------------
# Calibrated for real throughput ~1600 sims/sec (8 workers under tournament load)
TIERS = {
    'blitz': {
        'N_CANDIDATES': 7,
        'K_SIMS': 150,
        'ES_SE_THRESHOLD': 1.5,
        'ES_MIN_SIMS': 20,
        'NEAR_ENDGAME_TIME': 3.0,
        'MC_SKIP_MARGIN': 10.0,
    },
    'fast': {
        'N_CANDIDATES': 15,
        'K_SIMS': 400,
        'ES_SE_THRESHOLD': 1.2,
        'ES_MIN_SIMS': 50,
        'NEAR_ENDGAME_TIME': 5.0,
        'MC_SKIP_MARGIN': 8.0,
    },
    'standard': {
        'N_CANDIDATES': 30,
        'K_SIMS': 1500,
        'ES_SE_THRESHOLD': 0.8,
        'ES_MIN_SIMS': 80,
        'NEAR_ENDGAME_TIME': 15.0,
    },
    'deep': {
        'N_CANDIDATES': 35,
        'K_SIMS': 2000,
        'ES_SE_THRESHOLD': 0.5,
        'ES_MIN_SIMS': 100,
        'NEAR_ENDGAME_TIME': 15.0,
    },
}

# Fixed MC parameters
ES_CHECK_EVERY = 10         # Check convergence every N sims

# Dynamic worker count: cpu_threads - 3 (reserve for OS + opponent bot + main).
# 9 workers on 12-thread machine tested ~7% faster than 7 workers with no
# degradation on opponent throughput. Override with MC_WORKERS env var.
_mc_workers_env = os.environ.get('MC_WORKERS')
if _mc_workers_env:
    MC_WORKERS = int(_mc_workers_env)
else:
    MC_WORKERS = max(1, os.cpu_count() - 3)  # e.g. 12 threads -> 9 workers

# ---------------------------------------------------------------------------
# Optional overrides for N/K tuning (env vars)
# ---------------------------------------------------------------------------
_DADBOT_N = os.environ.get('DADBOT_N')           # Override N_CANDIDATES
_DADBOT_K = os.environ.get('DADBOT_K')           # Override K_SIMS

# Print active overrides at import time
_overrides = []
if _DADBOT_N: _overrides.append(f'N={_DADBOT_N}')
if _DADBOT_K: _overrides.append(f'K={_DADBOT_K}')
if _overrides:
    print(f'  [DadBot] Overrides: {", ".join(_overrides)}')

# MyBot's leave formula (for A/B testing SuperLeaves vs simple formula)
_MYBOT_TILE_VALUES = {
    '?': 20.0, 'S': 7.0, 'Z': 5.12, 'X': 3.31, 'R': 1.10, 'H': 0.60,
    'C': 0.85, 'M': 0.58, 'D': 0.45, 'E': 0.35, 'N': 0.22, 'T': -0.10,
    'L': 0.20, 'P': -0.46, 'K': -0.20, 'Y': -0.63, 'A': -0.63, 'J': -0.80,
    'B': -1.50, 'I': -2.07, 'F': -2.21, 'O': -2.50, 'G': -1.80, 'W': -4.50,
    'U': -4.00, 'V': -6.50, 'Q': -6.79,
}

def _mybot_leave_decay(tiles_in_bag):
    if tiles_in_bag >= 30:
        return 1.0
    elif tiles_in_bag >= 15:
        return 0.70
    elif tiles_in_bag >= 7:
        return 0.40
    else:
        return 0.10

def _mybot_leave_value(leave_str, bag_tiles=100):
    """MyBot's simple 26-char leave formula (for bisection testing)."""
    if not leave_str or leave_str == '-':
        return 0.0
    leave = leave_str.upper()
    value = sum(_MYBOT_TILE_VALUES.get(t, -1.0) for t in leave)
    vowels = sum(1 for t in leave if t in 'AEIOU')
    consonants = sum(1 for t in leave if t.isalpha() and t not in 'AEIOU' and t != '?')
    if len(leave) >= 2:
        if vowels == 1 and consonants >= 1:
            value += 2.0
        elif vowels >= 2 and consonants == 0:
            value -= 5.0
    value *= _mybot_leave_decay(bag_tiles)
    return value

# Bag parity penalty table (from crossplay engine)
_PARITY_P_OPP_EMPTIES = {
    1: 0.97, 2: 0.94, 3: 0.88, 4: 0.78,
    5: 0.62, 6: 0.40, 7: 0.18,
}
_PARITY_STRUCTURAL_ADV = 10.0

# Pre-computed tables
_TV = [0] * 26
for _ch, _val in TILE_VALUES.items():
    if _ch != '?':
        _TV[ord(_ch) - 65] = _val

_BONUS = [[(1, 1)] * 15 for _ in range(15)]
for (_r1, _c1), _btype in BONUS_SQUARES.items():
    _r0, _c0 = _r1 - 1, _c1 - 1
    if _btype == '2L':
        _BONUS[_r0][_c0] = (2, 1)
    elif _btype == '3L':
        _BONUS[_r0][_c0] = (3, 1)
    elif _btype == '2W':
        _BONUS[_r0][_c0] = (1, 2)
    elif _btype == '3W':
        _BONUS[_r0][_c0] = (1, 3)



# ---------------------------------------------------------------------------
# Leave evaluation -- bag-decay weighted tile value formula
# ---------------------------------------------------------------------------
# Replaces SuperLeaves (921K trained table). The trained table was built on a
# buggy engine (pre-V16 move finder fix) and has systematic biases that cause
# move quality to DEGRADE as N_CANDIDATES increases. The simple 26-char formula
# scales cleanly with N and slightly outperforms SuperLeaves at all tier levels.
# TODO: Retrain SuperLeaves on V20 engine and re-evaluate.
# ---------------------------------------------------------------------------

def _leave_value(leave_str, bag_empty=False, bag_tiles=100):
    """Evaluate leave quality using bag-decay weighted tile values."""
    return _mybot_leave_value(leave_str, bag_tiles)


# ---------------------------------------------------------------------------
# Main-process resources
# ---------------------------------------------------------------------------
_gdata_bytes = None
_word_set = None


def _ensure_resources():
    global _gdata_bytes, _word_set
    if _gdata_bytes is not None:
        return
    from engine.gaddag import get_gaddag
    _gdata_bytes = bytes(get_gaddag()._data)
    from engine.dictionary import get_dictionary
    _word_set = get_dictionary()._words


def _get_accel():
    if _CROSSPLAY_DIR not in sys.path:
        sys.path.insert(0, _CROSSPLAY_DIR)
    try:
        import gaddag_accel
        return gaddag_accel
    except ImportError:
        return None


# ---------------------------------------------------------------------------
# Unseen tile pool
# ---------------------------------------------------------------------------
def _compute_unseen(grid, my_rack, blanks_on_board):
    """Compute unseen tiles from grid (0-indexed) + rack + blanks."""
    counts = dict(TILE_DISTRIBUTION)
    bb_1idx = {(r, c) for r, c, _ in (blanks_on_board or [])}

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            tile = grid[r][c]
            if tile is not None:
                if (r + 1, c + 1) in bb_1idx:
                    counts['?'] = counts.get('?', 0) - 1
                else:
                    counts[tile] = counts.get(tile, 0) - 1

    for ch in my_rack.upper():
        counts[ch] = counts.get(ch, 0) - 1

    pool = []
    for letter, cnt in counts.items():
        for _ in range(max(0, cnt)):
            pool.append(letter)
    return pool


# ---------------------------------------------------------------------------
# 1-ply equity ranking (score + leave value)
# ---------------------------------------------------------------------------
def _rank_by_equity(moves, bag_tiles):
    """Sort moves by 1-ply equity = score + leave_value. Returns sorted list."""
    bag_empty = bag_tiles <= RACK_SIZE
    ranked = []
    for m in moves:
        leave = m.get('leave', '')
        lv = _leave_value(leave, bag_empty=bag_empty, bag_tiles=bag_tiles) if bag_tiles > 0 else 0.0
        ranked.append((m, m['score'] + lv, lv))
    ranked.sort(key=lambda x: -x[1])
    return ranked


# ===================================================================
# WORKER PROCESS CODE (runs in separate processes)
# ===================================================================

_w_gdata_bytes = None
_w_word_set = None
_w_accel = None
_w_tv = None
_w_bonus = None


def _worker_init(crossplay_dir, tournament_dir):
    """Initialize worker: load GADDAG + dictionary + Cython extension."""
    global _w_gdata_bytes, _w_word_set, _w_accel, _w_tv, _w_bonus

    if tournament_dir not in sys.path:
        sys.path.insert(0, tournament_dir)
    if crossplay_dir not in sys.path:
        sys.path.insert(0, crossplay_dir)

    from engine.gaddag import get_gaddag
    _w_gdata_bytes = bytes(get_gaddag()._data)

    from engine.dictionary import get_dictionary
    _w_word_set = get_dictionary()._words

    try:
        import gaddag_accel
        _w_accel = gaddag_accel
    except ImportError:
        _w_accel = None

    from engine.config import TILE_VALUES as TV, BONUS_SQUARES as BS
    _w_tv = [0] * 26
    for ch, val in TV.items():
        if ch != '?':
            _w_tv[ord(ch) - 65] = val

    _w_bonus = [[(1, 1)] * 15 for _ in range(15)]
    for (r1, c1), btype in BS.items():
        r0, c0 = r1 - 1, c1 - 1
        if btype == '2L':
            _w_bonus[r0][c0] = (2, 1)
        elif btype == '3L':
            _w_bonus[r0][c0] = (3, 1)
        elif btype == '2W':
            _w_bonus[r0][c0] = (1, 2)
        elif btype == '3W':
            _w_bonus[r0][c0] = (1, 3)


def _worker_eval_candidate(args):
    """Worker function: evaluate one candidate with K sims.

    Args tuple: (grid, bb_set_list, move, unseen_pool, k_sims, seed,
                  es_min_sims, es_check_every, es_se_threshold)
    """
    (grid, bb_set_list, move, unseen_pool, k_sims, seed,
     es_min_sims, es_check_every, es_se_threshold) = args

    random.seed(seed)

    from engine.config import VALID_TWO_LETTER, BINGO_BONUS, RACK_SIZE

    bb_set = set(bb_set_list)

    from engine.board import Board
    board = Board()
    for r in range(15):
        for c in range(15):
            if grid[r][c] is not None:
                board._grid[r][c] = grid[r][c]

    horizontal = move['direction'] == 'H'
    placed = board.place_move(move['word'], move['row'], move['col'], horizontal)

    blanks_used = move.get('blanks_used', [])
    if blanks_used:
        for bi in blanks_used:
            if horizontal:
                br, bc = move['row'] - 1, move['col'] - 1 + bi
            else:
                br, bc = move['row'] - 1 + bi, move['col'] - 1
            bb_set.add((br, bc))

    post_grid = board._grid
    pool_size = len(unseen_pool)
    rack_draw = min(RACK_SIZE, pool_size)

    use_cython = (_w_accel is not None and
                  hasattr(_w_accel, 'prepare_board_context') and
                  _w_gdata_bytes is not None)

    ctx = None
    if use_cython:
        ctx = _w_accel.prepare_board_context(
            post_grid, _w_gdata_bytes, bb_set,
            _w_word_set, VALID_TWO_LETTER,
            _w_tv, _w_bonus, BINGO_BONUS, RACK_SIZE,
        )

    running_sum = 0.0
    running_sum_sq = 0.0
    n_sims = 0

    for sim_i in range(k_sims):
        if n_sims >= es_min_sims and n_sims % es_check_every == 0:
            variance = (running_sum_sq / n_sims) - (running_sum / n_sims) ** 2
            if variance > 0:
                se = (variance / n_sims) ** 0.5
                if se < es_se_threshold:
                    break

        opp_rack = ''.join(random.sample(unseen_pool, rack_draw))

        if use_cython:
            opp_score, _, _, _, _ = _w_accel.find_best_score_c(ctx, opp_rack)
        else:
            blanks_1idx = [(r + 1, c + 1, '') for r, c in bb_set]
            opp_moves = get_legal_moves(board, opp_rack, blanks_1idx)
            opp_score = opp_moves[0]['score'] if opp_moves else 0

        running_sum += opp_score
        running_sum_sq += opp_score * opp_score
        n_sims += 1

    board.undo_move(placed)

    avg_opp = running_sum / n_sims if n_sims > 0 else 0.0
    return {
        'word': move['word'],
        'row': move['row'],
        'col': move['col'],
        'direction': move['direction'],
        'avg_opp': avg_opp,
        'n_sims': n_sims,
        'sum': running_sum,
        'sum_sq': running_sum_sq,
    }


# ===================================================================
# Endgame minimax worker (bag=0, parallel)
# ===================================================================

def _worker_eval_endgame(args):
    """Worker: deterministic minimax for one move when bag=0.

    Opponent rack is known exactly (unseen tiles = their rack).
    Evaluates: our_score - opponent_best_response.

    Args tuple: (grid, bb_set_list, move, opp_rack)
    """
    grid, bb_set_list, move, opp_rack = args

    from engine.config import VALID_TWO_LETTER, BINGO_BONUS, RACK_SIZE
    from engine.board import Board

    bb_set = set(bb_set_list)

    board = Board()
    for r in range(15):
        for c in range(15):
            if grid[r][c] is not None:
                board._grid[r][c] = grid[r][c]

    horizontal = move['direction'] == 'H'
    placed = board.place_move(move['word'], move['row'], move['col'], horizontal)

    # Update blank set with blanks from this move
    move_bb = set(bb_set)
    for bi in move.get('blanks_used', []):
        if horizontal:
            move_bb.add((move['row'] - 1, move['col'] - 1 + bi))
        else:
            move_bb.add((move['row'] - 1 + bi, move['col'] - 1))

    # Find opponent's best response
    use_cython = (_w_accel is not None and
                  hasattr(_w_accel, 'prepare_board_context') and
                  _w_gdata_bytes is not None)

    if use_cython:
        ctx = _w_accel.prepare_board_context(
            board._grid, _w_gdata_bytes, move_bb,
            _w_word_set, VALID_TWO_LETTER,
            _w_tv, _w_bonus, BINGO_BONUS, RACK_SIZE,
        )
        opp_score, _, _, _, _ = _w_accel.find_best_score_c(ctx, opp_rack)
    else:
        blanks_1idx = [(r + 1, c + 1, '') for r, c in move_bb]
        opp_moves = get_legal_moves(board, opp_rack, blanks_1idx)
        opp_score = opp_moves[0]['score'] if opp_moves else 0

    board.undo_move(placed)
    equity = move['score'] - opp_score

    return {
        'word': move['word'],
        'row': move['row'],
        'col': move['col'],
        'direction': move['direction'],
        'score': move['score'],
        'equity': equity,
    }


# ===================================================================
# Near-endgame worker (bag 1-8, parallel exhaustive 3-ply)
# ===================================================================

def _worker_eval_near_endgame(args):
    """Worker: exhaustive 3-ply for one bag-emptying move.

    Iterates over all C(unseen, rack_size) opponent rack combinations.
    For each: our_score - opp_best_response + our_follow_up.

    Args tuple: (grid, bb_set_list, move, unseen_pool, rack)
    """
    grid, bb_set_list, move, unseen_pool, rack = args

    from engine.config import VALID_TWO_LETTER, BINGO_BONUS, RACK_SIZE
    from engine.board import Board

    bb_set = set(bb_set_list)

    board = Board()
    for r in range(15):
        for c in range(15):
            if grid[r][c] is not None:
                board._grid[r][c] = grid[r][c]

    # Place our move (ply 1)
    horizontal = move['direction'] == 'H'
    placed = board.place_move(move['word'], move['row'], move['col'], horizontal)

    move_bb = set(bb_set)
    for bi in move.get('blanks_used', []):
        if horizontal:
            move_bb.add((move['row'] - 1, move['col'] - 1 + bi))
        else:
            move_bb.add((move['row'] - 1 + bi, move['col'] - 1))

    # Compute our leave (tiles remaining after playing this move)
    tiles_used = move.get('tiles_used', list(move['word']))
    rack_list = list(rack.upper())
    for t in tiles_used:
        if t in rack_list:
            rack_list.remove(t)
        elif '?' in rack_list:
            rack_list.remove('?')
    your_leave = ''.join(rack_list)

    use_cython = (_w_accel is not None and
                  hasattr(_w_accel, 'prepare_board_context') and
                  _w_gdata_bytes is not None)

    # Prepare board context for opponent response (ply 2)
    ctx_ply2 = None
    if use_cython:
        ctx_ply2 = _w_accel.prepare_board_context(
            board._grid, _w_gdata_bytes, move_bb,
            _w_word_set, VALID_TWO_LETTER,
            _w_tv, _w_bonus, BINGO_BONUS, RACK_SIZE,
        )

    unseen_str_list = list(unseen_pool)
    unseen_count = len(unseen_pool)
    opp_rack_size = min(RACK_SIZE, unseen_count)
    net_scores = []

    for combo_indices in combinations(range(unseen_count), opp_rack_size):
        opp_rack = ''.join(unseen_str_list[i] for i in combo_indices)
        drawn_indices = set(range(unseen_count)) - set(combo_indices)
        drawn_tiles = ''.join(unseen_str_list[i] for i in drawn_indices)
        your_full_rack = your_leave + drawn_tiles

        # Ply 2: opponent's best response
        if use_cython:
            opp_score, opp_word, opp_r, opp_c, opp_d = _w_accel.find_best_score_c(
                ctx_ply2, opp_rack)
        else:
            opp_score = 0
            opp_ms = get_legal_moves(board, opp_rack,
                                     [(r + 1, c + 1, '') for r, c in move_bb])
            if opp_ms:
                opp_score = opp_ms[0]['score']
                opp_word = opp_ms[0]['word']
                opp_r = opp_ms[0]['row']
                opp_c = opp_ms[0]['col']
                opp_d = opp_ms[0]['direction']

        # Ply 3: our follow-up after opponent's move
        your_resp_score = 0
        if opp_score > 0:
            opp_horiz = opp_d == 'H' if isinstance(opp_d, str) else opp_d
            placed_2 = board.place_move(opp_word, opp_r, opp_c, opp_horiz)

            if use_cython:
                ctx_ply3 = _w_accel.prepare_board_context(
                    board._grid, _w_gdata_bytes, move_bb,
                    _w_word_set, VALID_TWO_LETTER,
                    _w_tv, _w_bonus, BINGO_BONUS, RACK_SIZE,
                )
                your_resp_score, _, _, _, _ = _w_accel.find_best_score_c(
                    ctx_ply3, your_full_rack)
            else:
                resp_ms = get_legal_moves(board, your_full_rack,
                                          [(r + 1, c + 1, '') for r, c in move_bb])
                if resp_ms:
                    your_resp_score = resp_ms[0]['score']

            board.undo_move(placed_2)
        else:
            # Opponent passed -- use ply2 board state
            if use_cython:
                your_resp_score, _, _, _, _ = _w_accel.find_best_score_c(
                    ctx_ply2, your_full_rack)
            else:
                resp_ms = get_legal_moves(board, your_full_rack,
                                          [(r + 1, c + 1, '') for r, c in move_bb])
                if resp_ms:
                    your_resp_score = resp_ms[0]['score']

        net = move['score'] - opp_score + your_resp_score
        net_scores.append(net)

    board.undo_move(placed)

    avg_net = sum(net_scores) / len(net_scores) if net_scores else float(move['score'])

    return {
        'word': move['word'],
        'row': move['row'],
        'col': move['col'],
        'direction': move['direction'],
        'score': move['score'],
        'avg_equity': avg_net,
    }


# ===================================================================
# Near-endgame hybrid evaluator (bag 1-8)
# ===================================================================

def _evaluate_near_endgame(board, rack, moves, unseen_pool, blanks_on_board,
                           time_budget=15.0):
    """Hybrid evaluation for bag 1-8. Parallel.

    Bag-emptying moves: parallel exhaustive 3-ply via worker pool.
    Non-emptying moves: parity-adjusted 1-ply equity (instant, main process).

    Returns best move.
    """
    unseen_count = len(unseen_pool)
    bag_size = max(0, unseen_count - RACK_SIZE)

    results = []

    ranked = _rank_by_equity(moves, bag_size)
    candidates = ranked[:25]

    bb_set_list = [(r - 1, c - 1) for r, c, _ in (blanks_on_board or [])]
    grid = [row[:] for row in board._grid]

    # PASS 1: non-emptying moves (instant -- parity-adjusted 1-ply)
    exhaust_cands = []
    for move, equity_1ply, leave_val in candidates:
        tiles_used = move.get('tiles_used', [])
        n_used = len(tiles_used)

        if n_used >= bag_size:
            exhaust_cands.append((move, equity_1ply, leave_val))
        else:
            n_draw = min(n_used, bag_size)
            bag_after = bag_size - n_draw
            parity_penalty = 0.0
            if 1 <= bag_after <= 7:
                p_opp = _PARITY_P_OPP_EMPTIES.get(bag_after, 0.0)
                parity_penalty = -p_opp * _PARITY_STRUCTURAL_ADV

            results.append((move, equity_1ply + parity_penalty))

    # PASS 2: bag-emptying moves -- parallel exhaustive 3-ply via workers
    if exhaust_cands:
        work = []
        for move, equity_1ply, leave_val in exhaust_cands:
            move_data = {
                'word': move['word'],
                'row': move['row'],
                'col': move['col'],
                'direction': move['direction'],
                'score': move['score'],
                'blanks_used': move.get('blanks_used', []),
                'tiles_used': move.get('tiles_used', list(move['word'])),
            }
            work.append((grid, bb_set_list, move_data, unseen_pool, rack))

        pool = _get_pool()
        futures = [pool.submit(_worker_eval_near_endgame, w) for w in work]

        t_start = time.perf_counter()
        for i, future in enumerate(futures):
            remaining = time_budget - (time.perf_counter() - t_start)
            if remaining <= 0:
                # Time's up -- use 1-ply fallback for remaining candidates
                move, equity_1ply, _ = exhaust_cands[i]
                results.append((move, equity_1ply))
                continue
            try:
                result = future.result(timeout=max(1, remaining))
                # Find the original move object for this result
                orig_move = exhaust_cands[i][0]
                results.append((orig_move, result['avg_equity']))
            except Exception:
                move, equity_1ply, _ = exhaust_cands[i]
                results.append((move, equity_1ply))

    if not results:
        return moves[0] if moves else None

    results.sort(key=lambda x: -x[1])
    return results[0][0]


# ===================================================================
# DadBot class
# ===================================================================

_pool = None


def _get_pool():
    global _pool
    if _pool is None:
        print(f"  [DadBot] MC pool: {MC_WORKERS} workers "
              f"({os.cpu_count()} threads - 3 reserved)")
        _pool = ProcessPoolExecutor(
            max_workers=MC_WORKERS,
            initializer=_worker_init,
            initargs=(_CROSSPLAY_DIR, _TOURNAMENT_DIR),
        )
    return _pool


class DadBot(BaseEngine):

    def __init__(self):
        super().__init__()
        tier = os.environ.get('BOT_TIER', 'fast')
        self.config = TIERS.get(tier, TIERS['fast'])
        self.tier = tier

    @property
    def name(self):
        return "DadBot"

    def game_over(self, result, game_info):
        """Called when game ends. Pool kept alive for multi-game matches."""
        pass  # Workers persist -- GADDAG loaded once per pool lifetime

    def pick_move(self, board, rack, moves, game_info):
        if not moves:
            return None

        _ensure_resources()
        _DIAG = os.environ.get('DADBOT_TIMING', '')

        bag_tiles = game_info.get('tiles_in_bag', 1)
        blanks_on_board = game_info.get('blanks_on_board', [])
        grid = [row[:] for row in board._grid]
        cfg = self.config

        # ---------------------------------------------------------------
        # Endgame: bag=0, deterministic minimax
        # ---------------------------------------------------------------
        if bag_tiles == 0:
            return self._endgame_pick(board, rack, moves, blanks_on_board, grid)

        # ---------------------------------------------------------------
        # Near-endgame: bag 1-8, hybrid evaluation
        # ---------------------------------------------------------------
        if 1 <= bag_tiles <= 8:
            unseen_pool = _compute_unseen(grid, rack, blanks_on_board)
            return _evaluate_near_endgame(
                board, rack, moves, unseen_pool, blanks_on_board,
                time_budget=cfg.get('NEAR_ENDGAME_TIME', 15.0))

        # ---------------------------------------------------------------
        # Mid-game: parallel MC 2-ply with leave formula
        # ---------------------------------------------------------------
        t_move_start = time.perf_counter()
        unseen_pool = _compute_unseen(grid, rack, blanks_on_board)

        # Rank candidates by 1-ply equity (score + leave)
        t0 = time.perf_counter()
        ranked = _rank_by_equity(moves, bag_tiles)
        n_cands = int(_DADBOT_N) if _DADBOT_N else cfg['N_CANDIDATES']
        candidates = [(m, lv) for m, eq, lv in ranked[:n_cands]]
        t_rank = time.perf_counter() - t0

        # MC skip: if top 1-ply candidate leads by a wide margin, skip MC
        mc_skip_margin = cfg.get('MC_SKIP_MARGIN', 0)
        if mc_skip_margin > 0 and len(candidates) >= 2:
            top_eq = ranked[0][1]
            second_eq = ranked[1][1]
            if top_eq - second_eq >= mc_skip_margin:
                return candidates[0][0]

        # Build work items for MC (with tier-specific ES params)
        bb_set_list = [(r - 1, c - 1) for r, c, _ in (blanks_on_board or [])]
        k_sims = int(_DADBOT_K) if _DADBOT_K else cfg['K_SIMS']
        es_se = cfg['ES_SE_THRESHOLD']
        es_min = cfg.get('ES_MIN_SIMS', 30)

        work = []
        for i, (move, lv) in enumerate(candidates):
            move_data = {
                'word': move['word'],
                'row': move['row'],
                'col': move['col'],
                'direction': move['direction'],
                'score': move['score'],
                'blanks_used': move.get('blanks_used', []),
                'tiles_used': move.get('tiles_used', list(move['word'])),
            }
            seed = _rng.randint(0, 2**31)
            work.append((grid, bb_set_list, move_data, unseen_pool,
                         k_sims, seed, es_min, ES_CHECK_EVERY, es_se))

        # Fan out to worker pool
        t0 = time.perf_counter()
        pool = _get_pool()
        futures = [pool.submit(_worker_eval_candidate, w) for w in work]

        # Collect results and pick best
        best_move = None
        best_total = float('-inf')
        bag_empty_flag = bag_tiles <= RACK_SIZE
        total_sims = 0

        for i, future in enumerate(futures):
            result = future.result(timeout=60)
            avg_opp = result['avg_opp']
            n_sims = result.get('n_sims', 0)
            total_sims += n_sims
            move, leave_val = candidates[i]
            mc_equity = move['score'] - avg_opp

            leave = move.get('leave', '')
            lv = _leave_value(leave, bag_empty=bag_empty_flag, bag_tiles=bag_tiles) if bag_tiles > 0 else 0.0

            total = mc_equity + lv

            if total > best_total:
                best_total = total
                best_move = move

        t_mc = time.perf_counter() - t0
        t_total = time.perf_counter() - t_move_start

        # Timing diagnostics
        if _DIAG:
            sims_per_sec = total_sims / t_mc if t_mc > 0 else 0
            print(f"  [TIMING] rank={t_rank*1000:.0f}ms "
                  f"MC={t_mc*1000:.0f}ms({total_sims}sims,{sims_per_sec:.0f}/s) "
                  f"total={t_total*1000:.0f}ms "
                  f"bag={bag_tiles} cands={len(candidates)} "
                  f"moves={len(moves)}")

        return best_move

    def _endgame_pick(self, board, rack, moves, blanks_on_board, grid):
        """Deterministic endgame: opponent rack known exactly. Parallel.

        Exhaustive minimax over ALL legal moves -- no pruning. Each worker
        evaluates one move: our_score - opponent_best_response. Global time
        budget (180s) ensures we don't hang; if time runs out, best result
        so far is returned.
        """
        unseen = _compute_unseen(grid, rack, blanks_on_board)
        opp_rack = ''.join(unseen)

        bb_set_list = [(r - 1, c - 1) for r, c, _ in (blanks_on_board or [])]

        # Evaluate ALL legal moves (exhaustive minimax)
        work = []
        for move in moves:
            move_data = {
                'word': move['word'],
                'row': move['row'],
                'col': move['col'],
                'direction': move['direction'],
                'score': move['score'],
                'blanks_used': move.get('blanks_used', []),
            }
            work.append((grid, bb_set_list, move_data, opp_rack))

        # Fan out to worker pool
        pool = _get_pool()
        futures = [pool.submit(_worker_eval_endgame, w) for w in work]

        best_move = None
        best_equity = float('-inf')
        completed = 0
        timed_out = 0

        # Global time budget: 180s for all moves
        # (dense board: ~400 moves / 7 workers * ~2s each = ~114s typical)
        t_start = time.perf_counter()
        ENDGAME_BUDGET = 180.0

        for i, future in enumerate(futures):
            remaining = ENDGAME_BUDGET - (time.perf_counter() - t_start)
            if remaining <= 0:
                timed_out += len(futures) - i
                break
            try:
                result = future.result(timeout=max(2.0, remaining))
                completed += 1
            except Exception:
                timed_out += 1
                continue
            if result['equity'] > best_equity:
                best_equity = result['equity']
                best_move = moves[i]

        if timed_out:
            print(f"  [DadBot] Endgame: {completed}/{len(futures)} evaluated, "
                  f"{timed_out} timed out ({time.perf_counter() - t_start:.1f}s)")

        # Fallback: if nothing completed, play highest-scoring move
        if best_move is None:
            print("  [DadBot] Endgame: all workers failed, "
                  "falling back to top score")
            best_move = moves[0]

        return best_move

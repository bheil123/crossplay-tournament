"""
MyBot -- complete implementation with all 5 exercises + 1-ply simulation.

Strategy (Quackle-inspired):
  1. Greedy baseline: highest-scoring move
  2. Leave evaluation: keep blanks, S tiles, balanced rack
  3. Defensive heuristic: penalize opening bonus squares (used for candidate
     pre-filtering only -- simulation handles this implicitly)
  4. Endgame: when bag is empty, just maximize score
  5. Opponent modeling: track unseen tiles, adjust defensiveness when bag is small
  +  1-ply Monte Carlo: for each candidate move, sample random opponent racks
     and simulate their best response. Pick the move that minimizes the
     opponent's opportunity (inspired by Quackle's simulation engine).
"""

import os
import random
import time

from bots.base_engine import BaseEngine, get_legal_moves
from engine.config import BONUS_SQUARES, TILE_DISTRIBUTION

# Set MYBOT_VERBOSE=0 to suppress per-turn output (e.g. during tournament runs):
#   MYBOT_VERBOSE=0 python play_match.py --tournament --games 50
VERBOSE = os.environ.get('MYBOT_VERBOSE', '1') != '0'


# ---------------------------------------------------------------------------
# Tunable constants
# ---------------------------------------------------------------------------

N_CANDIDATES = 5   # Top moves (by static eval) to run through simulation
N_SAMPLES    = 20  # Simulated opponent racks per candidate move


# ---------------------------------------------------------------------------
# Exercise 2: Leave evaluation
# ---------------------------------------------------------------------------

LEAVE_VALUES = {
    '?': 25.0,
    'S':  8.0,
    'R':  2.0,
    'N':  1.5,
    'E':  1.0,
    'T':  1.0,
    'L':  0.5,
    'A':  0.5,
    'I':  0.0,
    'D':  0.0,
    'O': -0.5,
    'U': -1.5,
}

DUPLICATE_PENALTY = -3.0


def evaluate_leave(leave):
    value = 0.0
    seen = set()
    for tile in leave:
        value += LEAVE_VALUES.get(tile, -0.5)
        if tile in seen:
            value += DUPLICATE_PENALTY
        seen.add(tile)

    vowels     = sum(1 for t in leave if t in 'AEIOU')
    consonants = sum(1 for t in leave if t.isalpha() and t not in 'AEIOU')
    if len(leave) >= 3 and (vowels == 0 or consonants == 0):
        value -= 5.0

    return value


# ---------------------------------------------------------------------------
# Exercise 3: Defensive penalty (used for candidate pre-filtering only)
# ---------------------------------------------------------------------------

def _build_bonus_adjacency():
    adjacency = {}
    for (r, c), bonus_type in BONUS_SQUARES.items():
        if bonus_type in ('3W', '2W'):
            neighbors = []
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 1 <= nr <= 15 and 1 <= nc <= 15:
                    neighbors.append((nr, nc))
            adjacency[(r, c)] = (bonus_type, neighbors)
    return adjacency


BONUS_ADJACENCY = _build_bonus_adjacency()
OPEN_3W_PENALTY = -12.0
OPEN_2W_PENALTY = -5.0


def defensive_penalty(board, move):
    word       = move['word']
    row        = move['row']
    col        = move['col']
    horizontal = move['direction'] == 'H'

    filled = set()
    for i in range(len(word)):
        if horizontal:
            filled.add((row, col + i))
        else:
            filled.add((row + i, col))

    penalty = 0.0
    for (br, bc), (bonus_type, neighbors) in BONUS_ADJACENCY.items():
        if board.get_tile(br, bc) is not None:
            continue
        for nr, nc in neighbors:
            if (nr, nc) in filled:
                penalty += OPEN_3W_PENALTY if bonus_type == '3W' else OPEN_2W_PENALTY
                break

    return penalty


# ---------------------------------------------------------------------------
# Exercise 5: Opponent modeling -- unseen tiles
# ---------------------------------------------------------------------------

def unseen_tiles(board, rack, game_info):
    """Return a dict of tiles not on the board and not in our rack."""
    remaining = dict(TILE_DISTRIBUTION)

    blanks_on_board = {(r, c) for r, c, _ in game_info.get('blanks_on_board', [])}
    for row in range(1, 16):
        for col in range(1, 16):
            tile = board.get_tile(row, col)
            if tile is not None:
                key = '?' if (row, col) in blanks_on_board else tile.upper()
                remaining[key] = max(0, remaining.get(key, 0) - 1)

    for tile in rack:
        t = tile.upper()
        remaining[t] = max(0, remaining.get(t, 0) - 1)

    return {k: v for k, v in remaining.items() if v > 0}


def defensive_multiplier(unseen, game_info):
    """Scale defensive penalties higher when opponent likely holds blanks/S."""
    tiles_in_bag = game_info.get('tiles_in_bag', 100)
    if tiles_in_bag > 7:
        return 1.0

    total_unseen = sum(unseen.values())
    if total_unseen == 0:
        return 1.0

    opp_size = max(0, total_unseen - tiles_in_bag)
    if opp_size == 0:
        return 1.0

    blank_expected = unseen.get('?', 0) * opp_size / total_unseen
    s_expected     = unseen.get('S', 0) * opp_size / total_unseen

    return min(1.0 + blank_expected * 0.8 + s_expected * 0.2, 2.5)


# ---------------------------------------------------------------------------
# Static evaluation (used for candidate pre-filtering and simulation internals)
# ---------------------------------------------------------------------------

def static_eval(board, move, def_mult=1.0):
    return (move['score']
            + evaluate_leave(move.get('leave', ''))
            + defensive_penalty(board, move) * def_mult)


# ---------------------------------------------------------------------------
# Quackle-inspired 1-ply Monte Carlo simulation
# ---------------------------------------------------------------------------

def simulate_move(board, move, game_info, unseen_list):
    """
    Estimate the equity of a move by simulating opponent responses.

    Places `move` on the board, draws N_SAMPLES random opponent racks from
    unseen_list, finds each opponent's best static move, then undoes our move.

    Returns: our_score + leave_value - avg_opponent_score
    """
    our_score  = move['score']
    our_leave  = move.get('leave', '')

    # Build blanks_on_board after our move (needed for opponent's move gen)
    new_blanks = list(game_info.get('blanks_on_board', []))
    for idx in move.get('blanks_used', []):
        word, row, col = move['word'], move['row'], move['col']
        horizontal = move['direction'] == 'H'
        r = row if horizontal else row + idx
        c = col + idx if horizontal else col
        if board.is_empty(r, c):
            new_blanks.append((r, c, word[idx]))

    # Place our move (modifies board in place)
    placed = board.place_move(
        move['word'], move['row'], move['col'], move['direction'] == 'H'
    )

    opp_scores = []
    for _ in range(N_SAMPLES):
        random.shuffle(unseen_list)
        opp_rack  = ''.join(unseen_list[:min(7, len(unseen_list))])
        opp_moves = get_legal_moves(board, opp_rack, new_blanks)
        if opp_moves:
            best_opp = max(opp_moves, key=lambda m: m['score'] + evaluate_leave(m.get('leave', '')))
            opp_scores.append(best_opp['score'])
        else:
            opp_scores.append(0)

    board.undo_move(placed)

    avg_opp = sum(opp_scores) / len(opp_scores) if opp_scores else 0
    return our_score + evaluate_leave(our_leave) - avg_opp


# ---------------------------------------------------------------------------
# Bot
# ---------------------------------------------------------------------------

class MyBot(BaseEngine):

    def __init__(self):
        self._game_num    = 0
        self._game_start  = None
        self._turn_times  = []

    def game_over(self, result, game_info):
        self._game_num += 1
        if VERBOSE:
            elapsed  = time.time() - self._game_start if self._game_start else 0
            avg_turn = sum(self._turn_times) / len(self._turn_times) if self._turn_times else 0
            print(f"  Game {self._game_num} done ({result}) | "
                  f"{elapsed:.1f}s | avg turn {avg_turn:.2f}s")
        self._turn_times = []

    def pick_move(self, board, rack, moves, game_info):
        if not moves:
            return None

        if self._game_start is None:
            self._game_start = time.time()

        turn_start    = time.time()
        move_number   = game_info.get('move_number', '?')
        tiles_in_bag  = game_info.get('tiles_in_bag', 1)

        # Exercise 4: Endgame -- bag empty, just maximize score
        if tiles_in_bag == 0:
            return moves[0]

        # Exercise 5: unseen tiles for opponent modeling
        unseen   = unseen_tiles(board, rack, game_info)
        def_mult = defensive_multiplier(unseen, game_info)

        unseen_list = []
        for tile, count in unseen.items():
            unseen_list.extend([tile] * count)

        # Select top candidates by static eval (Exercises 2 + 3 + 5)
        candidates = sorted(
            moves[:25],
            key=lambda m: static_eval(board, m, def_mult),
            reverse=True
        )[:N_CANDIDATES]

        # If we have enough unseen tiles, run simulation
        if len(unseen_list) >= 7:
            if VERBOSE:
                print(f"  [G{self._game_num+1} T{move_number}] "
                      f"simulating {len(candidates)} cands x {N_SAMPLES} samples "
                      f"(bag={tiles_in_bag}, rack={rack})", end='', flush=True)

            best_move   = None
            best_equity = float('-inf')

            for move in candidates:
                equity = simulate_move(board, move, game_info, unseen_list)
                if equity > best_equity:
                    best_equity = equity
                    best_move   = move

            turn_elapsed = time.time() - turn_start
            self._turn_times.append(turn_elapsed)

            if VERBOSE:
                print(f" -> {best_move['word']} (eq={best_equity:+.1f}) | {turn_elapsed:.1f}s")

            return best_move

        # Fallback: static eval (very late game when bag nearly empty)
        return candidates[0]

"""
Strategy 5: Fast Monte Carlo simulation (Quackle-style).

Direct implementation of Maven/Quackle's core simulation strategy:
  1. Pick top N_CANDIDATES moves by static eval (Quackle leave values)
  2. For each candidate, sample N_SAMPLES random opponent racks
  3. Find opponent's best static response for each sample
  4. Pick move maximizing: our_score + our_leave_value - avg_opponent_score

Research basis: Sheppard (2002) — simulation provides "the deepest insight
into Scrabble positions." Maven uses ~300 iterations; we use N_SAMPLES=5
for speed (tradeoff: noisier but feasible in Python).

Only simulate mid-game (bag >= 15). Use static eval in endgame.
"""
import random
from bots.base_engine import BaseEngine, get_legal_moves
from engine.config import TILE_DISTRIBUTION

N_CANDIDATES = 5
N_SAMPLES    = 5

QUACKLE_TILE_VALUES = {
    '?': 25.57, 'S':  8.04, 'Z':  5.12, 'X':  3.31,
    'R':  1.10, 'H':  1.09, 'C':  0.85, 'M':  0.58,
    'D':  0.45, 'E':  0.35, 'N':  0.22, 'T': -0.10,
    'L': -0.17, 'P': -0.46, 'K': -0.54, 'Y': -0.63,
    'A': -0.63, 'J': -1.47, 'B': -2.00, 'I': -2.07,
    'F': -2.21, 'O': -2.50, 'G': -2.85, 'W': -3.82,
    'U': -5.10, 'V': -5.55, 'Q': -6.79,
}


def quackle_leave_value(leave, unseen=None):
    value = sum(QUACKLE_TILE_VALUES.get(t, -1.0) for t in leave)
    vowels = sum(1 for t in leave if t in 'AEIOU')
    consonants = sum(1 for t in leave if t.isalpha() and t not in 'AEIOU' and t != '?')
    if len(leave) >= 2:
        if vowels == 1 and consonants >= 1:
            value += 2.0
        elif vowels >= 2 and consonants == 0:
            value -= 5.0
    if 'Q' in leave and unseen is not None and unseen.get('U', 0) == 0:
        value -= 8.0
    return value


def unseen_tiles(board, rack, game_info):
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


def _simulate(board, move, unseen_list, game_info):
    """Place move, sample N_SAMPLES opponent racks, return avg opponent score."""
    new_blanks = list(game_info.get('blanks_on_board', []))
    for idx in move.get('blanks_used', []):
        word, row, col = move['word'], move['row'], move['col']
        horiz = move['direction'] == 'H'
        r = row if horiz else row + idx
        c = col + idx if horiz else col
        if board.is_empty(r, c):
            new_blanks.append((r, c, word[idx]))

    placed = board.place_move(move['word'], move['row'], move['col'],
                              move['direction'] == 'H')
    opp_scores = []
    for _ in range(N_SAMPLES):
        random.shuffle(unseen_list)
        opp_rack  = ''.join(unseen_list[:min(7, len(unseen_list))])
        opp_moves = get_legal_moves(board, opp_rack, new_blanks)
        if opp_moves:
            best = max(opp_moves,
                       key=lambda m: m['score'] + quackle_leave_value(m.get('leave', '')))
            opp_scores.append(best['score'])
        else:
            opp_scores.append(0)

    board.undo_move(placed)
    return sum(opp_scores) / len(opp_scores) if opp_scores else 0.0


class BotFastSim(BaseEngine):
    def pick_move(self, board, rack, moves, game_info):
        if not moves:
            return None
        tiles_in_bag = game_info.get('tiles_in_bag', 1)
        if tiles_in_bag == 0:
            return moves[0]

        unseen = unseen_tiles(board, rack, game_info)

        # Static-eval ranking for candidate selection
        candidates = sorted(
            moves[:20],
            key=lambda m: m['score'] + quackle_leave_value(m.get('leave', ''), unseen),
            reverse=True
        )[:N_CANDIDATES]

        # Skip simulation near endgame (too few tiles for meaningful sampling)
        if tiles_in_bag < 15:
            return candidates[0]

        unseen_list = [t for t, cnt in unseen.items() for _ in range(cnt)]

        best_move   = None
        best_equity = float('-inf')

        for move in candidates:
            avg_opp = _simulate(board, move, unseen_list, game_info)
            equity  = (move['score']
                       + quackle_leave_value(move.get('leave', ''), unseen)
                       - avg_opp)
            if equity > best_equity:
                best_equity = equity
                best_move   = move

        return best_move or candidates[0]

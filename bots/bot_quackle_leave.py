"""
Strategy 1: Quackle-calibrated leave values.

Implements the exact single-tile leave values from Quackle/Maven research
(Sheppard 2002, O'Laughlin calibration), plus:
  - Vowel/consonant balance adjustments
  - Q-without-U penalty when no U remains in unseen tiles
  - Defensive penalty for opening bonus squares

Key research insight: vowels are much more negative than naive intuition
suggests (A=-0.63, I=-2.07, O=-2.50, U=-5.10). High-value tiles like
Z (5.12) and X (3.31) are worth keeping.
"""
import random
from bots.base_engine import BaseEngine
from engine.config import BONUS_SQUARES, TILE_DISTRIBUTION

# ---------------------------------------------------------------------------
# Quackle single-tile leave values (O'Laughlin calibration)
# ---------------------------------------------------------------------------
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
    """Research-calibrated leave evaluation with balance adjustments."""
    value = sum(QUACKLE_TILE_VALUES.get(t, -1.0) for t in leave)

    # Vowel/consonant balance bonus (O'Laughlin)
    vowels = sum(1 for t in leave if t in 'AEIOU')
    consonants = sum(1 for t in leave if t.isalpha() and t not in 'AEIOU' and t != '?')
    if len(leave) >= 2:
        if vowels == 1 and consonants >= 1:
            value += 2.0   # balanced leave bonus
        elif vowels >= 2 and consonants == 0:
            value -= 5.0   # pure-vowel glut penalty

    # Q without U: nearly unplayable
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


def _build_bonus_adjacency():
    adj = {}
    for (r, c), btype in BONUS_SQUARES.items():
        if btype in ('3W', '2W'):
            neighbors = [(r+dr, c+dc) for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]
                         if 1 <= r+dr <= 15 and 1 <= c+dc <= 15]
            adj[(r, c)] = (btype, neighbors)
    return adj

BONUS_ADJ = _build_bonus_adjacency()


def defensive_penalty(board, move):
    word, row, col = move['word'], move['row'], move['col']
    horiz = move['direction'] == 'H'
    filled = {(row, col+i) if horiz else (row+i, col) for i in range(len(word))}
    penalty = 0.0
    for (br, bc), (btype, neighbors) in BONUS_ADJ.items():
        if board.get_tile(br, bc) is not None:
            continue
        if any(n in filled for n in neighbors):
            penalty += -12.0 if btype == '3W' else -5.0
    return penalty


class BotQuackleLeave(BaseEngine):
    def pick_move(self, board, rack, moves, game_info):
        if not moves:
            return None
        tiles_in_bag = game_info.get('tiles_in_bag', 1)
        if tiles_in_bag == 0:
            return moves[0]

        unseen = unseen_tiles(board, rack, game_info)
        return max(
            moves[:25],
            key=lambda m: (m['score']
                           + quackle_leave_value(m.get('leave', ''), unseen)
                           + defensive_penalty(board, m))
        )

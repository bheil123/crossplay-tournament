"""
LeaveBot -- Exercise 2 solution: score + leave quality.

Instead of just picking the highest-scoring move, consider what tiles
you keep (your "leave"). Blanks and S tiles are extremely valuable --
they enable future bingos (all 7 tiles, +40 bonus) and hooks.

The evaluation is: score + leave_bonus

To test:
    python play_match.py leave_bot greedy_bot --games 100
"""

from bots.base_engine import BaseEngine
from engine.config import TILE_VALUES


# How much each tile is worth to KEEP on your rack
# Higher = you'd rather keep it than spend it
LEAVE_VALUES = {
    '?': 25.0,   # Blanks are incredibly valuable -- keep them if possible
    'S': 8.0,    # S hooks onto almost any word for easy points
    'E': 1.0,    # Common, flexible
    'A': 0.5,    # Common vowel
    'I': 0.0,    # Okay
    'O': -0.5,   # Slightly overweight in the bag
    'U': -1.5,   # Hard to use
    'R': 2.0,    # Great consonant
    'N': 1.5,    # Flexible
    'T': 1.0,    # Common, good
    'L': 0.5,    # Decent
    'D': 0.0,    # Average
}

# Penalty for duplicate tiles (having 2+ of the same letter is bad)
DUPLICATE_PENALTY = -3.0


def evaluate_leave(leave):
    """Score the quality of leftover tiles."""
    value = 0.0

    # Sum individual tile values
    for tile in leave:
        value += LEAVE_VALUES.get(tile, -0.5)  # Unknown tiles slightly negative

    # Penalize duplicates
    seen = set()
    for tile in leave:
        if tile in seen:
            value += DUPLICATE_PENALTY
        seen.add(tile)

    # Bonus for balanced vowel/consonant ratio
    vowels = sum(1 for t in leave if t in 'AEIOU')
    consonants = sum(1 for t in leave if t.isalpha() and t not in 'AEIOU')
    if len(leave) >= 3:
        if vowels == 0 or consonants == 0:
            value -= 5.0  # All vowels or all consonants is terrible

    return value


class LeaveBot(BaseEngine):

    def pick_move(self, board, rack, moves, game_info):
        if not moves:
            return None

        best_move = None
        best_value = float('-inf')

        for move in moves:
            leave = move.get('leave', '')
            value = move['score'] + evaluate_leave(leave)

            if value > best_value:
                best_value = value
                best_move = move

        return best_move

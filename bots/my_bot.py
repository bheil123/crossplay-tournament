"""
MyBot -- YOUR engine goes here!

Start by beating RandomBot. The simplest winning strategy:
just pick the highest-scoring move every time. Then get fancier
from there.

Exercises (in order of difficulty):
  1. Beat RandomBot: pick the highest-scoring move
  2. Consider your leave: blanks and S tiles are valuable to keep
  3. Don't open bonus squares: avoid giving opponent 3W/2W access
  4. Endgame: when the bag is empty, leave value doesn't matter
"""

from bots.base_engine import BaseEngine


LEAVE_VALUES = {
    '?': 25.0,
    'S': 8.0,
    'R': 2.0,
    'N': 1.5,
    'E': 1.0,
    'T': 1.0,
    'L': 0.5,
    'A': 0.5,
    'I': 0.0,
    'D': 0.0,
    'O': -0.5,
    'U': -1.5,
}

DUPLICATE_PENALTY = -3.0


def evaluate_leave(leave):
    value = 0.0

    for tile in leave:
        value += LEAVE_VALUES.get(tile, -0.5)

    # Penalize duplicate tiles
    seen = set()
    for tile in leave:
        if tile in seen:
            value += DUPLICATE_PENALTY
        seen.add(tile)

    # Penalize all-vowel or all-consonant leaves
    vowels = sum(1 for t in leave if t in 'AEIOU')
    consonants = sum(1 for t in leave if t.isalpha() and t not in 'AEIOU')
    if len(leave) >= 3 and (vowels == 0 or consonants == 0):
        value -= 5.0

    return value


class MyBot(BaseEngine):

    def pick_move(self, board, rack, moves, game_info):
        if not moves:
            return None

        # Exercise 2: Pick the move with the best score + leave quality.
        return max(moves, key=lambda m: m['score'] + evaluate_leave(m['leave']))

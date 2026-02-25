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


class MyBot(BaseEngine):

    def pick_move(self, board, rack, moves, game_info):
        if not moves:
            return None

        # YOUR STRATEGY HERE
        # Right now this just picks a random move (same as RandomBot).
        # Change this to beat RandomBot!

        import random
        return random.choice(moves)

"""
RandomBot -- picks a random legal move.

This is the bot to beat first! It plays any valid move at random,
with no strategy at all. A bot that simply picks the highest-scoring
move will crush it.
"""

import random
from bots.base_engine import BaseEngine


class RandomBot(BaseEngine):
    """Picks a random legal move. No strategy whatsoever."""

    def pick_move(self, board, rack, moves, game_info):
        if not moves:
            return None
        return random.choice(moves)

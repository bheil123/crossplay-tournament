"""
GreedyBot -- Exercise 1 solution: pick the highest-scoring move every time.

This is the simplest winning strategy vs RandomBot. It typically wins
85-90% of games because higher-scoring moves compound over 15-20 turns.

To test:
    python play_match.py greedy_bot random_bot --games 100
"""

from bots.base_engine import BaseEngine


class GreedyBot(BaseEngine):

    def pick_move(self, board, rack, moves, game_info):
        if not moves:
            return None

        # Moves are already sorted by score (highest first)
        return moves[0]

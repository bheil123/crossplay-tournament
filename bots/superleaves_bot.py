"""
SuperLeavesBot -- Uses trained SuperLeaves table from the crossplay engine.

The crossplay engine trained leave values over 1M+ self-play games using
TD-learning (gen3). This bot uses those trained values to evaluate
score + leave_value for each candidate move, picking the best combination.

This is equivalent to 1-ply evaluation with trained leaves -- no Monte
Carlo simulation, no threat analysis. Just better leave evaluation than
hand-tuned formulas.
"""

import os
import pickle
from bots.base_engine import BaseEngine

# Path to the deployed SuperLeaves table
_LEAVES_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'engine', 'data', 'deployed_leaves.pkl'
)

_table = None


def _load_table():
    global _table
    if _table is not None:
        return _table
    with open(os.path.normpath(_LEAVES_PATH), 'rb') as f:
        _table = pickle.load(f)
    return _table


def leave_value(leave_str):
    """Look up trained leave value. Key is sorted tuple of uppercase letters."""
    table = _load_table()
    key = tuple(sorted(leave_str.upper()))
    return table.get(key, 0.0)


class SuperLeavesBot(BaseEngine):

    @property
    def name(self):
        return "SuperLeavesBot"

    def pick_move(self, board, rack, moves, game_info):
        if not moves:
            return None

        bag_empty = game_info.get('tiles_in_bag', 1) == 0

        best_move = None
        best_value = float('-inf')

        for move in moves:
            leave = move.get('leave', '')

            if bag_empty:
                # Endgame: leave doesn't matter, just maximize score
                value = move['score']
            else:
                value = move['score'] + leave_value(leave)

            if value > best_value:
                best_value = value
                best_move = move

        return best_move

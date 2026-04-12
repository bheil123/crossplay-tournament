"""
FormulaBot -- Uses the crossplay engine's research-derived leave formula.

Same greedy strategy as SuperLeavesBot (score + leave_value, no MC)
but uses the hand-tuned research formula from leave_eval.py instead of
a trained table. This is the "smart formula" with per-tile values from
MAGPIE/Quackle research, adjusted for Crossplay rules, plus interaction
terms (V:C balance, duplicate penalties, Q-without-U, bingo stems).
"""

import os
import sys
from bots.base_engine import BaseEngine

# Ensure crossplay package is importable
_crossplay_root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                '..', 'crossplay')
if os.path.isdir(_crossplay_root) and _crossplay_root not in sys.path:
    sys.path.insert(0, _crossplay_root)

_eval_fn = None
_loaded = False


def _load():
    global _eval_fn, _loaded
    if _loaded:
        return
    _loaded = True
    try:
        from crossplay.leave_eval import _research_evaluate
        _eval_fn = _research_evaluate
        print("  [FormulaBot] Research leave formula loaded")
    except Exception as e:
        print(f"  [FormulaBot] Failed to load research formula: {e}")


class FormulaBot(BaseEngine):

    @property
    def name(self):
        return "FormulaBot"

    def pick_move(self, board, rack, moves, game_info):
        if not moves:
            return None

        _load()
        bag_size = game_info.get('tiles_in_bag', 1)
        bag_empty = bag_size == 0

        best_move = None
        best_value = float('-inf')

        for move in moves:
            leave = move.get('leave', '')

            if bag_empty:
                value = move['score']
            elif _eval_fn is not None:
                value = move['score'] + _eval_fn(leave, bag_size=bag_size)
            else:
                value = move['score']

            if value > best_value:
                best_value = value
                best_move = move

        return best_move

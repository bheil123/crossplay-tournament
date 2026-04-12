"""
MagpieLeavesBot -- Uses MAGPIE's C-level KLV leave values.

Same greedy strategy as SuperLeavesBot (score + leave_value, no MC)
but uses the MAGPIE-trained leave values via the C bridge instead of
the Python-side SuperLeaves table.

This isolates the effect of MAGPIE leaves vs SuperLeaves training.
"""

import os
import sys
from bots.base_engine import BaseEngine

# Ensure crossplay package is importable
_crossplay_root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                '..', 'crossplay')
if os.path.isdir(_crossplay_root) and _crossplay_root not in sys.path:
    sys.path.insert(0, _crossplay_root)

_leave_fn = None
_loaded = False


def _load():
    global _leave_fn, _loaded
    if _loaded:
        return
    _loaded = True
    try:
        from crossplay.magpie_movefinder import leave_value, init, is_available
        if init() and is_available():
            _leave_fn = leave_value
            print("  [MagpieLeavesBot] MAGPIE C leave values loaded")
        else:
            print("  [MagpieLeavesBot] MAGPIE bridge not available, falling back to 0")
    except Exception as e:
        print(f"  [MagpieLeavesBot] Failed to load MAGPIE leaves: {e}")


def magpie_leave_value(leave_str):
    """Look up leave value via MAGPIE C KLV."""
    _load()
    if _leave_fn is None:
        return 0.0
    return _leave_fn(leave_str)


class MagpieLeavesBot(BaseEngine):

    @property
    def name(self):
        return "MagpieLeavesBot"

    def pick_move(self, board, rack, moves, game_info):
        if not moves:
            return None

        _load()
        bag_empty = game_info.get('tiles_in_bag', 1) == 0

        best_move = None
        best_value = float('-inf')

        for move in moves:
            leave = move.get('leave', '')

            if bag_empty:
                value = move['score']
            else:
                # Convert leave string to MAGPIE format (? for blanks)
                value = move['score'] + magpie_leave_value(leave)

            if value > best_value:
                best_value = value
                best_move = move

        return best_move

"""
DefensiveBot -- Exercise 3 solution: avoid opening bonus squares.

Builds on LeaveBot by penalizing moves that give the opponent access
to Triple Word (3W) and Double Word (2W) squares. A 40-point move that
opens a 3W for the opponent might be worse than a 25-point move that
doesn't.

To test:
    python play_match.py defensive_bot leave_bot --games 100
"""

from bots.base_engine import BaseEngine
from engine.config import BONUS_SQUARES


# Squares adjacent to each bonus square that, if filled, would give
# the opponent access to the bonus. We precompute these once.
def _build_bonus_adjacency():
    """For each bonus square, find all adjacent squares."""
    adjacency = {}
    for (r, c), bonus_type in BONUS_SQUARES.items():
        if bonus_type in ('3W', '2W'):
            neighbors = []
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 1 <= nr <= 15 and 1 <= nc <= 15:
                    neighbors.append((nr, nc))
            adjacency[(r, c)] = (bonus_type, neighbors)
    return adjacency


BONUS_ADJACENCY = _build_bonus_adjacency()

# Penalties for opening bonus squares
OPEN_3W_PENALTY = -12.0
OPEN_2W_PENALTY = -5.0

# Leave values (same as LeaveBot)
LEAVE_VALUES = {
    '?': 25.0, 'S': 8.0, 'E': 1.0, 'A': 0.5, 'R': 2.0,
    'N': 1.5, 'T': 1.0, 'L': 0.5,
}
DUPLICATE_PENALTY = -3.0


def evaluate_leave(leave):
    """Score the quality of leftover tiles."""
    value = 0.0
    seen = set()
    for tile in leave:
        value += LEAVE_VALUES.get(tile, -0.5)
        if tile in seen:
            value += DUPLICATE_PENALTY
        seen.add(tile)

    vowels = sum(1 for t in leave if t in 'AEIOU')
    consonants = sum(1 for t in leave if t.isalpha() and t not in 'AEIOU')
    if len(leave) >= 3 and (vowels == 0 or consonants == 0):
        value -= 5.0

    return value


def defensive_penalty(board, move):
    """Penalize moves that open bonus squares for the opponent."""
    word = move['word']
    row = move['row']
    col = move['col']
    horizontal = move['direction'] == 'H'

    # Find all squares this move fills
    filled = set()
    for i in range(len(word)):
        if horizontal:
            filled.add((row, col + i))
        else:
            filled.add((row + i, col))

    penalty = 0.0

    # Check each bonus square
    for (br, bc), (bonus_type, neighbors) in BONUS_ADJACENCY.items():
        # Skip if the bonus square is already occupied
        if board.get_tile(br, bc) is not None:
            continue

        # Check if any of our newly placed tiles are adjacent to this bonus
        for nr, nc in neighbors:
            if (nr, nc) in filled:
                # We're placing a tile next to an open bonus square
                if bonus_type == '3W':
                    penalty += OPEN_3W_PENALTY
                elif bonus_type == '2W':
                    penalty += OPEN_2W_PENALTY
                break  # Only penalize each bonus square once

    return penalty


class DefensiveBot(BaseEngine):

    def pick_move(self, board, rack, moves, game_info):
        if not moves:
            return None

        bag_empty = game_info.get('tiles_in_bag', 1) == 0

        best_move = None
        best_value = float('-inf')

        for move in moves:
            leave = move.get('leave', '')

            # Base: score + leave quality
            value = move['score'] + evaluate_leave(leave)

            # Defensive: penalize opening bonus squares
            # (skip in endgame -- no point being defensive when game is ending)
            if not bag_empty:
                value += defensive_penalty(board, move)

            if value > best_value:
                best_value = value
                best_move = move

        return best_move

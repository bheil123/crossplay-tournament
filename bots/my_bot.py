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
  5. Opponent modeling: track what tiles they might have
"""

from bots.base_engine import BaseEngine
from engine.config import BONUS_SQUARES, TILE_DISTRIBUTION


# ---------------------------------------------------------------------------
# Exercise 2: Leave evaluation
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Exercise 3: Defensive penalty -- don't open bonus squares
# ---------------------------------------------------------------------------

def _build_bonus_adjacency():
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
OPEN_3W_PENALTY = -12.0
OPEN_2W_PENALTY = -5.0


def defensive_penalty(board, move):
    word = move['word']
    row = move['row']
    col = move['col']
    horizontal = move['direction'] == 'H'

    filled = set()
    for i in range(len(word)):
        if horizontal:
            filled.add((row, col + i))
        else:
            filled.add((row + i, col))

    penalty = 0.0
    for (br, bc), (bonus_type, neighbors) in BONUS_ADJACENCY.items():
        if board.get_tile(br, bc) is not None:
            continue
        for nr, nc in neighbors:
            if (nr, nc) in filled:
                if bonus_type == '3W':
                    penalty += OPEN_3W_PENALTY
                elif bonus_type == '2W':
                    penalty += OPEN_2W_PENALTY
                break

    return penalty


# ---------------------------------------------------------------------------
# Exercise 5: Opponent modeling
# ---------------------------------------------------------------------------

def unseen_tiles(board, rack, game_info):
    """Tiles not on the board and not in our rack (in bag + opponent's hand)."""
    remaining = dict(TILE_DISTRIBUTION)

    blanks_on_board = {(r, c) for r, c, _ in game_info.get('blanks_on_board', [])}
    for row in range(1, 16):
        for col in range(1, 16):
            tile = board.get_tile(row, col)
            if tile is not None:
                if (row, col) in blanks_on_board:
                    remaining['?'] = max(0, remaining.get('?', 0) - 1)
                else:
                    t = tile.upper()
                    remaining[t] = max(0, remaining.get(t, 0) - 1)

    for tile in rack:
        t = tile.upper()
        remaining[t] = max(0, remaining.get(t, 0) - 1)

    return {k: v for k, v in remaining.items() if v > 0}


def defensive_multiplier(board, rack, game_info):
    """Scale defensive penalties up when opponent likely holds dangerous tiles."""
    tiles_in_bag = game_info.get('tiles_in_bag', 100)
    if tiles_in_bag > 7:
        return 1.0

    unseen = unseen_tiles(board, rack, game_info)
    total_unseen = sum(unseen.values())
    if total_unseen == 0:
        return 1.0

    opp_size = max(0, total_unseen - tiles_in_bag)
    if opp_size == 0:
        return 1.0

    # Expected number of dangerous tiles in opponent's hand
    blank_expected = unseen.get('?', 0) * opp_size / total_unseen
    s_expected = unseen.get('S', 0) * opp_size / total_unseen

    return min(1.0 + blank_expected * 0.8 + s_expected * 0.2, 2.5)


# ---------------------------------------------------------------------------
# Bot
# ---------------------------------------------------------------------------

class MyBot(BaseEngine):

    def pick_move(self, board, rack, moves, game_info):
        if not moves:
            return None

        # Exercise 4: Endgame -- bag empty, leave quality is irrelevant, just score
        if game_info.get('tiles_in_bag', 1) == 0:
            return moves[0]

        # Exercise 5: Scale defensive penalty by how dangerous opponent's tiles are
        def_mult = defensive_multiplier(board, rack, game_info)

        best_move = None
        best_value = float('-inf')

        for move in moves:
            # Exercise 2: score + leave quality
            value = move['score'] + evaluate_leave(move.get('leave', ''))
            # Exercise 3: penalize opening bonus squares (scaled by Ex. 5)
            value += defensive_penalty(board, move) * def_mult

            if value > best_value:
                best_value = value
                best_move = move

        return best_move

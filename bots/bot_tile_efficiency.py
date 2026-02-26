"""
Strategy 2: Tile efficiency / turnover.

From Maven's "tile turnover value" concept: cycling through tiles is
intrinsically valuable because the bag contains better tiles on average
than a stale, vowel-heavy rack.

Key idea: reward playing more tiles. A 6-tile play that scores 2 points
less than a 2-tile play is often BETTER because you draw 4 fresh tiles.
Also: detect vowel gluts and aggressively dump them.

Formula: score + leave_value + TURNOVER_BONUS * (tiles_played - 1)
Plus: extra vowel-dump bonus when rack has 4+ vowels.
"""
from bots.base_engine import BaseEngine
from engine.config import TILE_DISTRIBUTION

QUACKLE_TILE_VALUES = {
    '?': 25.57, 'S':  8.04, 'Z':  5.12, 'X':  3.31,
    'R':  1.10, 'H':  1.09, 'C':  0.85, 'M':  0.58,
    'D':  0.45, 'E':  0.35, 'N':  0.22, 'T': -0.10,
    'L': -0.17, 'P': -0.46, 'K': -0.54, 'Y': -0.63,
    'A': -0.63, 'J': -1.47, 'B': -2.00, 'I': -2.07,
    'F': -2.21, 'O': -2.50, 'G': -2.85, 'W': -3.82,
    'U': -5.10, 'V': -5.55, 'Q': -6.79,
}

TURNOVER_BONUS = 1.8   # per tile played beyond the first
VOWEL_DUMP_BONUS = 2.5  # extra per vowel played when rack has vowel glut


def quackle_leave_value(leave):
    value = sum(QUACKLE_TILE_VALUES.get(t, -1.0) for t in leave)
    vowels = sum(1 for t in leave if t in 'AEIOU')
    consonants = sum(1 for t in leave if t.isalpha() and t not in 'AEIOU' and t != '?')
    if len(leave) >= 2:
        if vowels == 1 and consonants >= 1:
            value += 2.0
        elif vowels >= 2 and consonants == 0:
            value -= 5.0
    return value


def tile_efficiency_eval(rack, move):
    """Score + leave + turnover bonus + vowel-dump bonus."""
    tiles_used = move.get('tiles_used', [])
    leave = move.get('leave', '')
    n_played = len(tiles_used)

    # Base: score + calibrated leave
    value = move['score'] + quackle_leave_value(leave)

    # Turnover bonus: reward playing more tiles
    value += max(0, n_played - 1) * TURNOVER_BONUS

    # Vowel glut: rack has 4+ vowels → dump vowels aggressively
    rack_vowels = sum(1 for t in rack if t in 'AEIOU')
    if rack_vowels >= 4:
        vowels_played = sum(1 for t in tiles_used if t in 'AEIOU')
        value += vowels_played * VOWEL_DUMP_BONUS

    return value


class BotTileEfficiency(BaseEngine):
    def pick_move(self, board, rack, moves, game_info):
        if not moves:
            return None
        tiles_in_bag = game_info.get('tiles_in_bag', 1)
        if tiles_in_bag == 0:
            return moves[0]

        return max(moves[:30], key=lambda m: tile_efficiency_eval(rack, m))

"""
Strategy 4: Endgame expert.

Calibrated leave values (Quackle) for mid-game, but switches to
PERFECT-INFORMATION MINIMAX when the bag is empty.

Research basis (Sheppard 2002): Maven's B* algorithm achieves 7-9 point
improvements over naive endgame play. When the bag is empty, we know
EXACTLY what tiles the opponent holds (unseen = their rack), so we can
do a real 1-ply minimax:

  For each of our candidate moves:
    Place it → find opponent's best response → undo
    Net equity = our_score - opponent_best_score

Pick the move with the best net equity.

Pre-endgame (bag < 10): defensive mode — lock down the board.
Mid-game: Quackle leave values + defensive penalty.
"""
from bots.base_engine import BaseEngine, get_legal_moves
from engine.config import TILE_DISTRIBUTION, BONUS_SQUARES

QUACKLE_TILE_VALUES = {
    '?': 25.57, 'S':  8.04, 'Z':  5.12, 'X':  3.31,
    'R':  1.10, 'H':  1.09, 'C':  0.85, 'M':  0.58,
    'D':  0.45, 'E':  0.35, 'N':  0.22, 'T': -0.10,
    'L': -0.17, 'P': -0.46, 'K': -0.54, 'Y': -0.63,
    'A': -0.63, 'J': -1.47, 'B': -2.00, 'I': -2.07,
    'F': -2.21, 'O': -2.50, 'G': -2.85, 'W': -3.82,
    'U': -5.10, 'V': -5.55, 'Q': -6.79,
}


def quackle_leave_value(leave, unseen=None):
    value = sum(QUACKLE_TILE_VALUES.get(t, -1.0) for t in leave)
    vowels = sum(1 for t in leave if t in 'AEIOU')
    consonants = sum(1 for t in leave if t.isalpha() and t not in 'AEIOU' and t != '?')
    if len(leave) >= 2:
        if vowels == 1 and consonants >= 1:
            value += 2.0
        elif vowels >= 2 and consonants == 0:
            value -= 5.0
    if 'Q' in leave and unseen is not None and unseen.get('U', 0) == 0:
        value -= 8.0
    return value


def unseen_tiles(board, rack, game_info):
    remaining = dict(TILE_DISTRIBUTION)
    blanks_on_board = {(r, c) for r, c, _ in game_info.get('blanks_on_board', [])}
    for row in range(1, 16):
        for col in range(1, 16):
            tile = board.get_tile(row, col)
            if tile is not None:
                key = '?' if (row, col) in blanks_on_board else tile.upper()
                remaining[key] = max(0, remaining.get(key, 0) - 1)
    for tile in rack:
        t = tile.upper()
        remaining[t] = max(0, remaining.get(t, 0) - 1)
    return {k: v for k, v in remaining.items() if v > 0}


def _build_bonus_adj():
    adj = {}
    for (r, c), btype in BONUS_SQUARES.items():
        if btype in ('3W', '2W'):
            neighbors = [(r+dr, c+dc) for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]
                         if 1 <= r+dr <= 15 and 1 <= c+dc <= 15]
            adj[(r, c)] = (btype, neighbors)
    return adj

BONUS_ADJ = _build_bonus_adj()


def defensive_penalty(board, move):
    word, row, col = move['word'], move['row'], move['col']
    horiz = move['direction'] == 'H'
    filled = {(row, col+i) if horiz else (row+i, col) for i in range(len(word))}
    penalty = 0.0
    for (br, bc), (btype, neighbors) in BONUS_ADJ.items():
        if board.get_tile(br, bc) is not None:
            continue
        if any(n in filled for n in neighbors):
            penalty += -12.0 if btype == '3W' else -5.0
    return penalty


def _endgame_minimax(board, moves, opp_rack, game_info):
    """Perfect-info 1-ply minimax: pick move that minimizes opponent's best reply."""
    blanks_on_board = list(game_info.get('blanks_on_board', []))
    best_move   = None
    best_equity = float('-inf')

    for move in moves[:12]:
        new_blanks = list(blanks_on_board)
        for idx in move.get('blanks_used', []):
            word, row, col = move['word'], move['row'], move['col']
            horiz = move['direction'] == 'H'
            r = row if horiz else row + idx
            c = col + idx if horiz else col
            if board.is_empty(r, c):
                new_blanks.append((r, c, word[idx]))

        placed = board.place_move(move['word'], move['row'], move['col'],
                                  move['direction'] == 'H')
        opp_moves = get_legal_moves(board, opp_rack, new_blanks)
        best_opp_score = max((m['score'] for m in opp_moves), default=0)
        board.undo_move(placed)

        equity = move['score'] - best_opp_score
        if equity > best_equity:
            best_equity = equity
            best_move   = move

    return best_move


class BotEndgameExpert(BaseEngine):
    def pick_move(self, board, rack, moves, game_info):
        if not moves:
            return None

        tiles_in_bag = game_info.get('tiles_in_bag', 1)
        unseen = unseen_tiles(board, rack, game_info)

        # --- Perfect information endgame (bag empty) ---
        if tiles_in_bag == 0:
            opp_rack = ''.join(t * cnt for t, cnt in unseen.items())[:7]
            if opp_rack:
                return _endgame_minimax(board, moves, opp_rack, game_info)
            return moves[0]

        # --- Pre-endgame (bag < 10): defensive, lock board down ---
        if tiles_in_bag < 10:
            return max(
                moves[:20],
                key=lambda m: (m['score']
                               + quackle_leave_value(m.get('leave', ''), unseen)
                               + defensive_penalty(board, m) * 2.0)  # stronger defense
            )

        # --- Mid-game: calibrated leave + defense ---
        return max(
            moves[:25],
            key=lambda m: (m['score']
                           + quackle_leave_value(m.get('leave', ''), unseen)
                           + defensive_penalty(board, m))
        )

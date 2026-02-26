# CLAUDE.md -- Crossplay Engine Tournament

## What is this?

A tournament kit for building Crossplay (word game) bots. You write a bot
in `bots/my_bot.py` that picks moves, then test it against other bots.

**Your goal:** Beat RandomBot first, then get fancier.

## Quick start

```bash
# Watch a game between two random bots
python play_match.py random_bot random_bot --watch

# Run 100 games and see who wins
python play_match.py random_bot random_bot --games 100

# Test YOUR bot against RandomBot
python play_match.py my_bot random_bot --games 100

# Round-robin tournament of all bots in bots/
python play_match.py --tournament --games 50
```

First run builds the word dictionary index (~48 seconds). After that it
loads in under 1 second.

## Your bot file: bots/my_bot.py

Your bot extends `BaseEngine` and implements one method: `pick_move()`.

```python
class MyBot(BaseEngine):
    def pick_move(self, board, rack, moves, game_info):
        # moves is a list of legal moves, sorted by score (highest first)
        # Return one of them, or None to pass
        return moves[0]  # This picks the highest-scoring move
```

That's it! The engine generates all legal moves for you. You just pick
which one to play.

## What pick_move() receives

### board
A Board object. Query tiles with:
- `board.get_tile(row, col)` -- returns letter or None (1-indexed, 1-15)
- `board.is_empty(row, col)` -- True if square is empty

### rack
A string of your tiles, e.g. `"AEINRST"`. Blanks are `"?"`.

### moves
A list of move dicts, sorted by score (highest first). Each dict has:

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `word` | str | `"QUARTZ"` | The word played |
| `row` | int | `8` | Starting row (1-indexed) |
| `col` | int | `6` | Starting column (1-indexed) |
| `direction` | str | `"H"` | `"H"` (horizontal) or `"V"` (vertical) |
| `score` | int | `48` | Total points including bonuses |
| `tiles_used` | list | `["Q","U","A","R","T","Z"]` | Tiles consumed from your rack |
| `leave` | str | `"I"` | Remaining rack tiles after playing |
| `blanks_used` | list | `[2]` | Indices in word where blanks are used |

### game_info
A dict with game state:

| Field | Type | Description |
|-------|------|-------------|
| `your_score` | int | Your current score |
| `opp_score` | int | Opponent's current score |
| `tiles_in_bag` | int | Tiles remaining in the bag |
| `move_number` | int | Current move number (1-based) |
| `blanks_on_board` | list | `[(row, col, letter), ...]` for blanks on board |

## Exercises (progressive difficulty)

### Exercise 1: Beat RandomBot
**Goal:** Win 80%+ of games against RandomBot.

**Hint:** The simplest strategy that works -- just pick the highest-scoring
move every time. Since `moves` is already sorted by score, this is literally
`return moves[0]`.

**Test:** `python play_match.py my_bot random_bot --games 100`

### Exercise 2: Consider your leave
**Goal:** Beat the greedy strategy by keeping good tiles.

**Concept:** After you play a word, the tiles left on your rack (your "leave")
matter for future turns. Some tiles are much more valuable to keep:
- **Blanks (?):** Worth ~25 extra points to keep (they enable bingos)
- **S tiles:** Worth ~8 extra points (hook onto almost any word)
- **Duplicate tiles:** Bad -- having 3 E's is worse than having E, R, N

**Approach:** Instead of `max(score)`, evaluate `score + leave_quality`:
```python
def leave_value(leave):
    value = 0
    for tile in leave:
        if tile == '?': value += 25
        elif tile == 'S': value += 8
        elif tile in 'RNTLE': value += 1
        elif tile in 'UWV': value -= 2
    return value
```

**Test:** `python play_match.py my_bot greedy_bot --games 100`
(Compare against `examples/greedy_bot.py` to make sure you're winning.)

### Exercise 3: Don't open bonus squares
**Goal:** Beat the leave strategy by playing defensively.

**Concept:** The board has Triple Word (3W) and Double Word (2W) bonus
squares. If your move places a tile next to an open 3W square, your
opponent might use it for a huge score next turn.

**Approach:** Add a penalty for moves that open bonus squares:
```python
from engine.config import BONUS_SQUARES

# Check if the move places tiles adjacent to an open 3W or 2W
for bonus_pos, bonus_type in BONUS_SQUARES.items():
    if bonus_type == '3W' and is_adjacent_to_new_tile(bonus_pos, move):
        value -= 12  # Penalty for opening a 3W
```

**Test:** `python play_match.py my_bot leave_bot --games 100`

### Exercise 4: Endgame strategy
**Goal:** Play optimally when the bag is empty.

**Concept:** When `game_info['tiles_in_bag'] == 0`, there are no more
tiles to draw. Leave quality doesn't matter anymore -- just maximize
your score for the remaining turns.

**Crossplay endgame rules:** Both players get one final turn after the
bag empties. Leftover tiles do NOT count against you (unlike Scrabble).

### Exercise 5: Opponent modeling
**Goal:** Track what tiles the opponent might have.

**Concept:** 100 tiles total in the game. You know what's on the board
and in your rack. The remaining tiles are split between the bag and the
opponent's rack. When the bag gets small, you can narrow down what they
might hold.

## Common patterns

### Pick the highest-scoring move
```python
return moves[0]  # Already sorted by score
```

### Pick the best move by a custom metric
```python
best = max(moves, key=lambda m: m['score'] + my_leave_value(m['leave']))
return best
```

### Filter moves by word length
```python
long_moves = [m for m in moves if len(m['tiles_used']) >= 5]
return long_moves[0] if long_moves else moves[0]
```

### Check if a move uses a blank
```python
uses_blank = [m for m in moves if '?' in m['tiles_used']]
```

### Look for bingos (use all 7 tiles, +40 bonus)
```python
bingos = [m for m in moves if len(m['tiles_used']) == 7]
if bingos:
    return bingos[0]  # Play the bingo!
```

### Check score difference
```python
spread = game_info['your_score'] - game_info['opp_score']
if spread < -50:
    # We're losing -- take risks, go for big plays
    return moves[0]
```

### Query the board
```python
# What tile is at row 8, column 8?
tile = board.get_tile(8, 8)  # Returns 'E' or None

# Is a square empty?
if board.is_empty(8, 8):
    print("Center is open")
```

## Project structure

```
bots/
  base_engine.py   <- BaseEngine class (don't edit)
  random_bot.py    <- RandomBot: picks random moves
  my_bot.py        <- YOUR BOT (edit this!)
engine/            <- Game infrastructure (DO NOT EDIT)
examples/          <- Solution bots for the exercises
  greedy_bot.py    <- Exercise 1 solution
  leave_bot.py     <- Exercise 2 solution
  defensive_bot.py <- Exercise 3 solution
play_match.py      <- Match runner
```

## Rules quick reference

- 15x15 board, 100 tiles (including 3 blanks)
- Blanks are worth 0 points but can represent any letter
- 7 tiles on your rack
- Using all 7 tiles = "sweep" bonus of 40 points
- Both players get one final turn after bag empties
- Leftover tiles do NOT penalize you (different from Scrabble)

See RULES.md for full rules and bonus square layout.

## DO NOT EDIT

Everything in `engine/` is game infrastructure. Don't modify it.
Your code goes in `bots/my_bot.py` only.

The `examples/` folder has spoiler solutions -- look at them if you're
stuck, but try the exercises yourself first!

## Speed tiers (BOT_TIER)

The match runner supports a `--tier` flag that sets the `BOT_TIER`
environment variable before loading engines. Any bot can read this to
adjust how much time it spends thinking.

```bash
python play_match.py my_bot random_bot --tier standard
```

| Tier | Target avg/move | Typical settings | Use case |
|------|----------------|-----------------|----------|
| `blitz` | ~1s | N=15, K=500, SE=1.5 | Quick testing, 100+ game runs |
| `fast` | ~3s | N=25, K=1000, SE=1.0 | Default tournament play |
| `standard` | ~10s | N=40, K=2000, SE=0.7 | Full-strength evaluation |
| `deep` | ~30s | N=55, K=3000, SE=0.45 | Maximum strength |

**How to make your bot tier-aware (optional):**

```python
import os

class MyBot(BaseEngine):
    def __init__(self):
        tier = os.environ.get('BOT_TIER', 'fast')
        if tier == 'blitz':
            self.n_samples = 2
        elif tier == 'deep':
            self.n_samples = 50
        else:
            self.n_samples = 10
```

If your bot doesn't check `BOT_TIER`, it runs identically at all tiers.
The env var is a convention, not a requirement.

**Performance model (i7-8700, 8 MC workers):**
- MC time per move = `N_candidates * avg_sims / (workers * sims_per_sec)`
- ~350 sims/sec/worker average across a game
- Early stopping (SE threshold) controls actual sims: SE=1.5 -> ~140 avg,
  SE=1.0 -> ~300 avg, SE=0.7 -> ~612 avg, SE=0.45 -> ~1481 avg
- Positional heuristics (risk, blocking, DLS exposure): <25ms, always free
- Move generation (by match runner): ~0.1-0.3s fixed cost

## Debugging tips

- Use `--watch` to see the board after every move
- Add `print()` statements in your `pick_move()` to see what's happening
- `len(moves)` tells you how many legal moves exist
- `moves[0]['score']` is the highest possible score this turn
- If `not moves` is True, you have no legal moves (return None to pass)

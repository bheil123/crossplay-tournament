# Crossplay Rules

Crossplay is a word game played on a 15x15 board. It's similar to Scrabble
but with several important differences.

## Basics

- **Board:** 15x15 grid with bonus squares
- **Tiles:** 100 total (97 letters + 3 blanks)
- **Rack:** 7 tiles per player
- **Dictionary:** ~196,000 valid words (NASPA Word List)

## Tile Values and Distribution

| Tile | Value | Count | | Tile | Value | Count |
|------|-------|-------|-|------|-------|-------|
| A | 1 | 9 | | N | 1 | 5 |
| B | 4 | 2 | | O | 1 | 8 |
| C | 3 | 2 | | P | 3 | 2 |
| D | 2 | 4 | | Q | 10 | 1 |
| E | 1 | 12 | | R | 1 | 6 |
| F | 4 | 2 | | S | 1 | 5 |
| G | 4 | 3 | | T | 1 | 6 |
| H | 3 | 3 | | U | 2 | 3 |
| I | 1 | 8 | | V | 6 | 2 |
| J | 10 | 1 | | W | 5 | 2 |
| K | 6 | 1 | | X | 8 | 1 |
| L | 2 | 4 | | Y | 4 | 2 |
| M | 3 | 2 | | Z | 10 | 1 |
| ? | 0 | 3 | | | | |

**Key difference from Scrabble:** 3 blanks (not 2), and some tile values
differ (e.g., H=3, G=4, W=5 in Crossplay vs H=4, G=2, W=4 in Scrabble).

## Bonus Squares

```
    1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
 1| 3L .  .  3W .  .  .  2L .  .  .  3W .  .  3L
 2| .  2W .  .  .  .  3L .  3L .  .  .  .  2W .
 3| .  .  .  .  2L .  .  .  .  .  2L .  .  .  .
 4| 3W .  .  2L .  .  .  2W .  .  .  2L .  .  3W
 5| .  .  2L .  .  3L .  .  .  3L .  .  2L .  .
 6| .  .  .  .  3L .  .  2L .  .  3L .  .  .  .
 7| .  3L .  .  .  .  .  .  .  .  .  .  .  3L .
 8| 2L .  .  2W .  2L .  *  .  2L .  2W .  .  2L
 9| .  3L .  .  .  .  .  .  .  .  .  .  .  3L .
10| .  .  .  .  3L .  .  2L .  .  3L .  .  .  .
11| .  .  2L .  .  3L .  .  .  3L .  .  2L .  .
12| 3W .  .  2L .  .  .  2W .  .  .  2L .  .  3W
13| .  .  .  .  2L .  .  .  .  .  2L .  .  .  .
14| .  2W .  .  .  .  3L .  3L .  .  .  .  2W .
15| 3L .  .  3W .  .  .  2L .  .  .  3W .  .  3L
```

- **3L** = Triple Letter (tile value x3)
- **2L** = Double Letter (tile value x2)
- **3W** = Triple Word (word score x3)
- **2W** = Double Word (word score x2)
- **\*** = Center square (NO bonus in Crossplay)

**Key differences from Scrabble:** Different bonus square layout. The
center square has NO bonus (Scrabble gives 2W on center).

## Scoring

1. Add up tile values for each letter in the word
2. Apply letter bonuses (2L, 3L) to individual tiles
3. Apply word bonuses (2W, 3W) to the word total
4. Bonuses only count when a NEW tile is placed on that square
5. If a word crosses multiple word bonus squares, multiply all of them

### Sweep Bonus (Bingo)

Using all 7 tiles from your rack in one move earns a **40-point bonus**.
(Scrabble gives 50 points for this.)

### Cross-words

When you place tiles, any new words formed perpendicular to your main
word also count. Each cross-word is scored independently with its own
letter and word bonuses.

## Endgame

**Key difference from Scrabble:** When the tile bag empties:

1. Both players get **one final turn** each
2. **Leftover tiles do NOT penalize you** -- no subtraction for tiles
   remaining on your rack
3. There is no bonus for "going out" first

In Scrabble, the player who goes out gets double the opponent's remaining
tile values, and the opponent loses their remaining tile values. Crossplay
has none of this -- both players simply play their final turns and the
higher score wins.

## Game End Conditions

The game ends when:
- Both players have played their final turn after the bag emptied
- Four consecutive passes (both players pass twice in a row)
- No legal moves exist for either player

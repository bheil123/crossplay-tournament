# Crossplay Engine Tournament

Build a bot that plays Crossplay (a word game like Scrabble). Start by
beating the random bot, then climb the ladder!

## Setup

You need Python 3.10+ installed. No other dependencies required.

```bash
git clone <this-repo>
cd crossplay-tournament
```

## Your first game

Watch two random bots play:

```bash
python play_match.py random_bot random_bot --watch
```

The first run builds a word index (~48 seconds). After that it loads
instantly.

## Build your bot

Edit `bots/my_bot.py`. The starter code picks a random move -- change
it to pick better ones!

```bash
# Test your bot against RandomBot (100 games)
python play_match.py my_bot random_bot --games 100

# Watch a single game to see what your bot does
python play_match.py my_bot random_bot --watch
```

## Using Claude Code

Open this folder in Claude Code and ask it to help you build a bot.
It will read `CLAUDE.md` and know exactly how the tournament works.

Try: "Help me build a bot that beats RandomBot"

## Exercises

1. **Beat RandomBot** -- pick the highest-scoring move every time
2. **Leave quality** -- keep good tiles (blanks, S) for future turns
3. **Defense** -- avoid opening Triple Word squares for your opponent
4. **Endgame** -- maximize score when the bag is empty
5. **Opponent modeling** -- track what tiles they might have

Solution bots are in `examples/` if you get stuck.

## Match runner

```bash
python play_match.py BOT1 BOT2              # 10 games, show summary
python play_match.py BOT1 BOT2 --games 100  # 100 games
python play_match.py BOT1 BOT2 --watch      # watch 1 game visually
python play_match.py --tournament --games 50 # round-robin all bots
```

Bot names are the Python file names in `bots/` or `examples/`
(without the `.py`).

## Project structure

```
bots/my_bot.py     <- YOUR BOT (edit this!)
bots/random_bot.py <- The bot to beat first
examples/          <- Solution bots (spoilers!)
engine/            <- Game infrastructure (don't touch)
play_match.py      <- Match runner
CLAUDE.md          <- Context for Claude Code
RULES.md           <- Crossplay rules
```

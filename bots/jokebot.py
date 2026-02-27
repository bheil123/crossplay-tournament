"""
JokeBot -- a tournament bot that tells a joke before every move.

The punchline of each joke is the word JokeBot plays. Jokes feature
the family: Bill/Dad, Mom, Patrick, Katie, Madeleine, Julia.

Doesn't try hard to win -- picks the highest-scoring move that has
a joke available (within 60% of best score). If no joke exists for
any viable move, uses a template joke with the best-scoring move.

Usage:
    python play_match.py jokebot greedy_bot --watch
"""

import random
from bots.base_engine import BaseEngine
from bots.jokebot_jokes import get_joke, get_template_joke


class JokeBot(BaseEngine):
    """A bot that tells family-themed jokes. The punchline is the word played."""

    @property
    def name(self):
        return "JokeBot"

    def __init__(self):
        self.told_jokes = set()   # (WORD, joke_id) pairs already used
        self.jokes_told = 0
        self.games_played = 0

    def pick_move(self, board, rack, moves, game_info):
        if not moves:
            print("\n  JokeBot: I've got nothing... just like Patrick's homework folder.\n")
            return None

        best_score = moves[0]['score']
        # Accept moves within 60% of best (still fun, not throwing the game)
        threshold = max(best_score * 0.6, 5)

        # Gather viable moves and shuffle so we don't always tell the same jokes
        viable = [m for m in moves if m['score'] >= threshold]
        random.shuffle(viable)

        # Try to find a move with an untold joke
        for move in viable:
            joke = get_joke(move['word'], self.told_jokes)
            if joke:
                self.told_jokes.add((move['word'].upper(), joke['id']))
                self.jokes_told += 1
                print(f"\n  JokeBot: {joke['setup']}")
                return move

        # No curated joke available -- use a template with the highest-scoring move
        move = moves[0]
        template = get_template_joke(move['word'])
        self.jokes_told += 1
        print(f"\n  JokeBot: {template}")
        return move

    def game_over(self, result, game_info):
        self.games_played += 1
        print(f"\n  JokeBot told {self.jokes_told} jokes this game.")
        if result == 'win':
            print("  JokeBot: I WON?! Even Dad couldn't believe it.")
        elif result == 'loss':
            print("  JokeBot: I lost, but at least I was funnier than Patrick.")
        else:
            print("  JokeBot: A tie? That's like kissing your sister. Sorry, Katie.")
        print()

        # Reset for next game (keep told_jokes across games for variety)
        self.jokes_told = 0

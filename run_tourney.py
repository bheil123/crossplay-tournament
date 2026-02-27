"""Run DadBot vs MyBot tournament across all tiers."""
import subprocess
import sys
import datetime
import os
import random

PYTHON = sys.executable
SCRIPT = "play_match.py"
WORK_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(WORK_DIR, "tourney_results.txt")

TIERS = [
    ("blitz", 20),
    ("fast", 20),
    ("standard", 20),
    ("deep", 5),
]


def main():
    # Generate a master seed for the whole tournament (reproducible on replay)
    master_seed = random.randint(0, 2**31)

    with open(OUTPUT, "w") as f:
        f.write(f"=== DADBOT vs MYBOT TOURNAMENT ===\n")
        f.write(f"Started: {datetime.datetime.now()}\n")
        f.write(f"Master seed: {master_seed}\n\n")
        f.flush()

        for tier, games in TIERS:
            f.write(f"{'='*50}\n")
            f.write(f"TIER: {tier} ({games} games)\n")
            f.write(f"Started: {datetime.datetime.now()}\n")
            f.write(f"{'='*50}\n")
            f.flush()

            result = subprocess.run(
                [PYTHON, SCRIPT, "dadbot", "my_bot",
                 "--games", str(games), "--tier", tier,
                 "--seed", str(master_seed)],
                cwd=WORK_DIR,
                stdout=f,
                stderr=subprocess.STDOUT,
            )
            f.write(f"\nCompleted: {datetime.datetime.now()}\n")
            f.write(f"Exit code: {result.returncode}\n\n")
            f.flush()

        f.write(f"\n=== TOURNAMENT COMPLETE ===\n")
        f.write(f"Finished: {datetime.datetime.now()}\n")


if __name__ == "__main__":
    main()

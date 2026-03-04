"""Run 4-tier x 2-config matrix: formula vs blend(0.5) at blitz/fast/standard/deep.

Same seed across all runs for apple-to-apple comparison.
Results saved to tourney_tier_matrix.txt with all 8 runs combined.
"""
import subprocess
import sys
import os
import random
import datetime

PYTHON = sys.executable
WORK_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(WORK_DIR, "tourney_tier_matrix.txt")

MASTER_SEED = 777888999  # Fixed seed for reproducibility across all runs
GAMES = 20
OPPONENT = "my_bot"

TIERS = ['blitz', 'fast', 'standard', 'deep']
CONFIGS = [
    ('formula', {'DADBOT_LEAVES': 'formula'}),
    ('blend_05', {'DADBOT_LEAVES': 'blend', 'DADBOT_BLEND_ALPHA': '0.5'}),
]

def main():
    total_runs = len(TIERS) * len(CONFIGS)
    total_games = total_runs * GAMES
    started = datetime.datetime.now()

    with open(OUTPUT, "w") as f:
        f.write(f"=== DADBOT v6 TIER MATRIX TOURNAMENT ===\n")
        f.write(f"Started: {started}\n")
        f.write(f"Master seed: {MASTER_SEED}\n")
        f.write(f"Games per run: {GAMES}\n")
        f.write(f"Total runs: {total_runs} ({len(TIERS)} tiers x {len(CONFIGS)} configs)\n")
        f.write(f"Total games: {total_games}\n")
        f.write(f"Opponent: {OPPONENT}\n")
        f.write(f"Tiers: {', '.join(TIERS)}\n")
        f.write(f"Configs: {', '.join(c[0] for c in CONFIGS)}\n\n")
        f.flush()

        run_num = 0
        for tier in TIERS:
            for cfg_name, env_vars in CONFIGS:
                run_num += 1
                f.write(f"{'='*60}\n")
                f.write(f"RUN {run_num}/{total_runs}: {tier} + {cfg_name}\n")
                f.write(f"Started: {datetime.datetime.now()}\n")
                f.write(f"{'='*60}\n")
                f.flush()

                env = os.environ.copy()
                env['BOT_TIER'] = tier
                for k, v in env_vars.items():
                    env[k] = v

                # Generate same seeds for this tier+config
                # Use master seed so all runs get same game positions
                result = subprocess.run(
                    [PYTHON, "play_match.py", "dadbot_v6", OPPONENT,
                     "--games", str(GAMES), "--tier", tier,
                     "--seed", str(MASTER_SEED)],
                    cwd=WORK_DIR,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    env=env,
                )
                f.write(f"\nCompleted: {datetime.datetime.now()}\n")
                f.write(f"Exit code: {result.returncode}\n\n")
                f.flush()

                # Print progress to console
                elapsed = (datetime.datetime.now() - started).total_seconds()
                print(f"[{run_num}/{total_runs}] {tier}+{cfg_name} done "
                      f"(exit={result.returncode}, {elapsed:.0f}s elapsed)")

        f.write(f"\n=== TOURNAMENT COMPLETE ===\n")
        f.write(f"Finished: {datetime.datetime.now()}\n")
        total_time = (datetime.datetime.now() - started).total_seconds()
        f.write(f"Total time: {total_time:.0f}s ({total_time/60:.1f}min)\n")

    print(f"\nResults written to {OUTPUT}")
    print(f"Total time: {total_time/60:.1f} minutes")


if __name__ == "__main__":
    main()

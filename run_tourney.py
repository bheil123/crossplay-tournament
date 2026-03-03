"""Run DadBot v6 A/B tournament testing SuperLeaves and 3-ply features.

A/B test matrix (4 configurations, each vs dadbot_v5 baseline):
  1. formula + no-3ply  (V21 baseline -- should match v5)
  2. superleaves + no-3ply  (gen4 trained leaves only)
  3. formula + 3ply  (3-ply override only)
  4. superleaves + 3ply  (both features)

Usage:
    python run_tourney.py                    # Full A/B matrix (20 games each)
    python run_tourney.py --games 5          # Quick smoke test (5 games each)
    python run_tourney.py --config baseline  # Run single config only
    python run_tourney.py --tier fast        # Override tier (default: fast)
"""
import subprocess
import sys
import datetime
import os
import random
import argparse

PYTHON = sys.executable
SCRIPT = "play_match.py"
WORK_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(WORK_DIR, "tourney_results.txt")

# A/B test configurations: (label, DADBOT_LEAVES, DADBOT_3PLY)
AB_CONFIGS = {
    'baseline':     ('formula',      'off'),
    'superleaves':  ('superleaves',  'off'),
    '3ply':         ('formula',      'on'),
    'both':         ('superleaves',  'on'),
}

# Default: all configs
DEFAULT_CONFIGS = ['baseline', 'superleaves', '3ply', 'both']


def main():
    parser = argparse.ArgumentParser(description="DadBot v6 A/B Tournament")
    parser.add_argument('--games', type=int, default=20,
                        help="Games per A/B config (default: 20)")
    parser.add_argument('--config', choices=list(AB_CONFIGS.keys()),
                        help="Run single config only (default: all)")
    parser.add_argument('--tier', default='fast',
                        help="BOT_TIER for all configs (default: fast)")
    parser.add_argument('--opponent', default='dadbot_v5',
                        help="Opponent bot module (default: dadbot_v5)")
    parser.add_argument('--timing', action='store_true',
                        help="Enable DADBOT_TIMING diagnostics")
    args = parser.parse_args()

    configs = [args.config] if args.config else DEFAULT_CONFIGS
    games_per = args.games
    tier = args.tier

    # Generate master seed for reproducibility
    master_seed = random.randint(0, 2**31)
    rng = random.Random(master_seed)
    total_games = len(configs) * games_per
    all_seeds = [rng.randint(0, 2**31) for _ in range(total_games)]

    # Partition seeds across configs
    config_seeds = {}
    offset = 0
    for cfg_name in configs:
        config_seeds[cfg_name] = all_seeds[offset:offset + games_per]
        offset += games_per

    with open(OUTPUT, "w") as f:
        f.write(f"=== DADBOT v6 A/B TOURNAMENT ===\n")
        f.write(f"Started: {datetime.datetime.now()}\n")
        f.write(f"Master seed: {master_seed}\n")
        f.write(f"Tier: {tier}\n")
        f.write(f"Opponent: {args.opponent}\n")
        f.write(f"Games per config: {games_per}\n")
        f.write(f"Total games: {total_games}\n")
        f.write(f"Configs: {', '.join(configs)}\n\n")
        f.flush()

        for cfg_name in configs:
            leaves, three_ply = AB_CONFIGS[cfg_name]
            seeds = config_seeds[cfg_name]
            seeds_csv = ','.join(str(s) for s in seeds)

            f.write(f"{'='*60}\n")
            f.write(f"CONFIG: {cfg_name}  "
                    f"(DADBOT_LEAVES={leaves}, DADBOT_3PLY={three_ply})\n")
            f.write(f"Tier: {tier}, Games: {games_per}\n")
            f.write(f"Started: {datetime.datetime.now()}\n")
            f.write(f"{'='*60}\n")
            f.flush()

            # Set env vars for this config
            env = os.environ.copy()
            env['BOT_TIER'] = tier
            env['DADBOT_LEAVES'] = leaves
            env['DADBOT_3PLY'] = three_ply
            if args.timing:
                env['DADBOT_TIMING'] = '1'

            result = subprocess.run(
                [PYTHON, SCRIPT, "dadbot_v6", args.opponent,
                 "--games", str(games_per), "--tier", tier,
                 "--game-seeds", seeds_csv],
                cwd=WORK_DIR,
                stdout=f,
                stderr=subprocess.STDOUT,
                env=env,
            )
            f.write(f"\nCompleted: {datetime.datetime.now()}\n")
            f.write(f"Exit code: {result.returncode}\n\n")
            f.flush()

        f.write(f"\n=== TOURNAMENT COMPLETE ===\n")
        f.write(f"Finished: {datetime.datetime.now()}\n")

    print(f"Results written to {OUTPUT}")


if __name__ == "__main__":
    main()

"""Run DadBot v6 A/B tournament testing leave evaluation strategies.

A/B test matrix (3 configurations, each vs my_bot baseline):
  1. baseline     -- formula leaves (V21 baseline)
  2. superleaves  -- gen4 TD-trained leaves only
  3. blend        -- alpha * formula + (1-alpha) * superleaves

Usage:
    python run_tourney.py                    # Full A/B matrix (20 games each)
    python run_tourney.py --games 5          # Quick smoke test (5 games each)
    python run_tourney.py --config baseline  # Run single config only
    python run_tourney.py --tier fast        # Override tier (default: fast)
    python run_tourney.py --alpha 0.3        # Override blend alpha (default: 0.5)
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

# A/B test configurations: (label, DADBOT_LEAVES)
AB_CONFIGS = {
    'baseline':     'formula',
    'superleaves':  'superleaves',
    'blend':        'blend',
}

# Default: all configs
DEFAULT_CONFIGS = ['baseline', 'superleaves', 'blend']


def main():
    parser = argparse.ArgumentParser(description="DadBot v6 A/B Tournament")
    parser.add_argument('--games', type=int, default=20,
                        help="Games per A/B config (default: 20)")
    parser.add_argument('--config', choices=list(AB_CONFIGS.keys()),
                        help="Run single config only (default: all)")
    parser.add_argument('--tier', default='fast',
                        help="BOT_TIER for all configs (default: fast)")
    parser.add_argument('--opponent', default='my_bot',
                        help="Opponent bot module (default: my_bot)")
    parser.add_argument('--alpha', type=float, default=0.5,
                        help="Blend alpha (default: 0.5, 1=formula, 0=superleaves)")
    parser.add_argument('--seed', type=int, default=None,
                        help="Master seed for reproducibility (default: random)")
    parser.add_argument('--timing', action='store_true',
                        help="Enable DADBOT_TIMING diagnostics")
    args = parser.parse_args()

    configs = [args.config] if args.config else DEFAULT_CONFIGS
    games_per = args.games
    tier = args.tier

    # Generate master seed for reproducibility
    master_seed = args.seed if args.seed is not None else random.randint(0, 2**31)
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
            leaves = AB_CONFIGS[cfg_name]
            seeds = config_seeds[cfg_name]
            seeds_csv = ','.join(str(s) for s in seeds)

            alpha_str = f", DADBOT_BLEND_ALPHA={args.alpha}" if leaves == 'blend' else ""
            f.write(f"{'='*60}\n")
            f.write(f"CONFIG: {cfg_name}  "
                    f"(DADBOT_LEAVES={leaves}{alpha_str})\n")
            f.write(f"Tier: {tier}, Games: {games_per}\n")
            f.write(f"Started: {datetime.datetime.now()}\n")
            f.write(f"{'='*60}\n")
            f.flush()

            # Set env vars for this config
            env = os.environ.copy()
            env['BOT_TIER'] = tier
            env['DADBOT_LEAVES'] = leaves
            if leaves == 'blend':
                env['DADBOT_BLEND_ALPHA'] = str(args.alpha)
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

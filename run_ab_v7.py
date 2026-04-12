#!/usr/bin/env python3
"""
DadBot V7 A/B Test Matrix — test feature toggle combinations.

Runs DadBot v7 with different env var configurations against a fixed
opponent. All configs use the same seed sequence for direct comparison.

Usage:
    python run_ab_v7.py                              # Full matrix, 50 games, blitz
    python run_ab_v7.py --games 10                   # Quick smoke test
    python run_ab_v7.py --configs baseline,ne_only   # Specific configs
    python run_ab_v7.py --tier standard              # Override tier
    python run_ab_v7.py --opponent formula_bot        # Override opponent
    python run_ab_v7.py --list                        # List available configs
"""

import os
import sys
import time
import argparse
import subprocess


# ---------------------------------------------------------------------------
# A/B Test Configurations
# ---------------------------------------------------------------------------

AB_CONFIGS = {
    # Baseline: current v7 defaults (C MC, MAGPIE leaves, opening book, delegate endgame to v5)
    'baseline': {},

    # Near-endgame evaluator (v7's own, not delegated to v5)
    'ne_only': {
        'V7_NEAR_ENDGAME': '1',
    },

    # Bogowin at various blend factors
    'bogowin_0.0': {
        'V7_BOGOWIN': '1',
        'V7_BOGOWIN_BLEND': '0.0',
    },
    'bogowin_0.3': {
        'V7_BOGOWIN': '1',
        'V7_BOGOWIN_BLEND': '0.3',
    },
    'bogowin_0.5': {
        'V7_BOGOWIN': '1',
        'V7_BOGOWIN_BLEND': '0.5',
    },
    'bogowin_0.7': {
        'V7_BOGOWIN': '1',
        'V7_BOGOWIN_BLEND': '0.7',
    },

    # Tile tracker + Bogowin
    'tt_bogowin': {
        'V7_TILE_TRACKER': '1',
        'V7_BOGOWIN': '1',
        'V7_BOGOWIN_BLEND': '0.5',
    },

    # Near-endgame + Bogowin
    'ne_bogowin': {
        'V7_NEAR_ENDGAME': '1',
        'V7_BOGOWIN': '1',
        'V7_BOGOWIN_BLEND': '0.5',
    },

    # Full: all features enabled
    'full': {
        'V7_NEAR_ENDGAME': '1',
        'V7_TILE_TRACKER': '1',
        'V7_BOGOWIN': '1',
        'V7_BOGOWIN_BLEND': '0.5',
    },

    # Leave source comparisons
    'leaves_formula': {
        'V7_LEAVES': 'formula',
    },
    'leaves_superleaves': {
        'V7_LEAVES': 'superleaves',
    },

    # No opening book
    'no_ob': {
        'V7_OPENING_BOOK': '0',
    },

    # Python MC (v5 path, for comparison)
    'mc_python': {
        'V7_MC': 'python',
    },
}

DEFAULT_CONFIGS = [
    'baseline', 'ne_only',
    'bogowin_0.0', 'bogowin_0.3', 'bogowin_0.5', 'bogowin_0.7',
    'ne_bogowin', 'full',
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CROSSPLAY_ROOT = os.path.join(os.path.dirname(SCRIPT_DIR), 'crossplay')
RESULTS_FILE = os.path.join(SCRIPT_DIR, 'ab_v7_results.txt')


def run_config(config_name, config_env, opponent, games, seed, tier):
    """Run one A/B configuration. Returns parsed results dict."""
    env = os.environ.copy()
    env['PYTHONPATH'] = CROSSPLAY_ROOT
    env['PYTHONUNBUFFERED'] = '1'
    env['BOT_TIER'] = tier

    # Apply config-specific env vars
    for k, v in config_env.items():
        env[k] = v

    cmd = [
        sys.executable, '-u', 'play_match.py',
        'dadbot_v7', opponent,
        '--games', str(games),
        '--seed', str(seed),
        '--tier', tier,
    ]

    print(f"\n{'='*60}", flush=True)
    print(f"  Config: {config_name}", flush=True)
    env_str = ', '.join(f'{k}={v}' for k, v in config_env.items()) if config_env else '(defaults)'
    print(f"  Env: {env_str}", flush=True)
    print(f"{'='*60}", flush=True)

    t0 = time.time()
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=SCRIPT_DIR, env=env
    )
    elapsed = time.time() - t0

    output = result.stdout + result.stderr
    print(output[-500:] if len(output) > 500 else output, flush=True)

    # Parse results from output
    parsed = {
        'config': config_name,
        'wins': 0, 'losses': 0, 'ties': 0,
        'spread': 0.0, 'v7_avg': 0.0, 'opp_avg': 0.0,
        'move_time': 0.0, 'elapsed': elapsed,
    }

    for line in output.split('\n'):
        if 'DadBot-v7 wins:' in line:
            parts = line.split('|')
            for p in parts:
                p = p.strip()
                if 'DadBot-v7 wins:' in p:
                    parsed['wins'] = int(p.split(':')[1].strip())
                elif 'wins:' in p:
                    parsed['losses'] = int(p.split(':')[1].strip())
                elif 'Ties:' in p:
                    parsed['ties'] = int(p.split(':')[1].strip())
        elif 'Avg spread:' in line:
            try:
                parsed['spread'] = float(line.split(':')[1].strip())
            except (ValueError, IndexError):
                pass
        elif 'DadBot-v7 avg:' in line:
            try:
                parts = line.split('|')
                parsed['v7_avg'] = float(parts[0].split(':')[1].strip())
                parsed['opp_avg'] = float(parts[1].split(':')[1].strip())
            except (ValueError, IndexError):
                pass
        elif 'DadBot-v7: avg' in line:
            try:
                parsed['move_time'] = float(line.split('avg')[1].split('s')[0].strip())
            except (ValueError, IndexError):
                pass

    return parsed


def main():
    parser = argparse.ArgumentParser(description='DadBot V7 A/B Test Matrix')
    parser.add_argument('--games', type=int, default=50, help='Games per config')
    parser.add_argument('--seed', type=int, default=42, help='Master seed')
    parser.add_argument('--tier', default='blitz', help='Bot tier')
    parser.add_argument('--opponent', default='superleaves_bot', help='Opponent bot')
    parser.add_argument('--configs', default=None,
                        help='Comma-separated config names (default: all)')
    parser.add_argument('--list', action='store_true', help='List available configs')
    args = parser.parse_args()

    if args.list:
        print("Available A/B configs:")
        for name, env in AB_CONFIGS.items():
            env_str = ', '.join(f'{k}={v}' for k, v in env.items()) if env else '(defaults)'
            default = ' [DEFAULT]' if name in DEFAULT_CONFIGS else ''
            print(f"  {name:20s} {env_str}{default}")
        return

    if args.configs:
        config_names = [c.strip() for c in args.configs.split(',')]
        for c in config_names:
            if c not in AB_CONFIGS:
                print(f"Unknown config: {c}. Use --list to see available configs.")
                return
    else:
        config_names = DEFAULT_CONFIGS

    print(f"DadBot V7 A/B Test Matrix")
    print(f"  Configs: {len(config_names)}")
    print(f"  Games per config: {args.games}")
    print(f"  Tier: {args.tier}")
    print(f"  Opponent: {args.opponent}")
    print(f"  Seed: {args.seed}")

    t_total = time.time()
    results = []

    with open(RESULTS_FILE, 'w') as f:
        f.write(f"DadBot V7 A/B Test — {args.games} games each, seed {args.seed}, "
                f"tier {args.tier}, vs {args.opponent}\n")
        f.write(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*70}\n\n")

    for config_name in config_names:
        config_env = AB_CONFIGS[config_name]
        parsed = run_config(config_name, config_env, args.opponent,
                            args.games, args.seed, args.tier)
        results.append(parsed)

        with open(RESULTS_FILE, 'a') as f:
            wlt = f"{parsed['wins']}-{parsed['losses']}-{parsed['ties']}"
            f.write(f"{config_name:20s} {wlt:>10s} {parsed['spread']:>+8.1f} "
                    f"{parsed['v7_avg']:>7.1f} {parsed['move_time']:>6.2f}s "
                    f"{parsed['elapsed']:>7.0f}s\n")

    total_elapsed = time.time() - t_total

    # Print summary table
    print(f"\n\n{'='*70}")
    print(f"  A/B TEST SUMMARY  ({args.games} games each, {args.tier} tier)")
    print(f"{'='*70}")
    print(f"  {'Config':20s} {'W-L-T':>10s} {'Spread':>8s} {'V7 Avg':>7s} {'Move':>6s}")
    print(f"  {'-'*55}")

    for r in results:
        wlt = f"{r['wins']}-{r['losses']}-{r['ties']}"
        print(f"  {r['config']:20s} {wlt:>10s} {r['spread']:>+8.1f} "
              f"{r['v7_avg']:>7.1f} {r['move_time']:>5.2f}s")

    print(f"\n  Total time: {total_elapsed/60:.0f} min")
    print(f"  Results saved to: {RESULTS_FILE}")

    with open(RESULTS_FILE, 'a') as f:
        f.write(f"\nTotal time: {total_elapsed/60:.0f} min\n")
        f.write(f"Finished: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")


if __name__ == '__main__':
    main()

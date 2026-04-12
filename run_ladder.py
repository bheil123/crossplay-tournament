#!/usr/bin/env python3
"""Run v7 ladder at multiple tiers. Results saved to ladder_results.txt."""

import os
import sys
import time
import subprocess

OPPONENTS = [
    'bot_quackle_leave',
    'magpie_leaves_bot',
    'leave_bot',
    'formula_bot',
    'superleaves_bot',
]

TIERS = ['blitz', 'standard']
GAMES = 50
SEED = 42

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CROSSPLAY_ROOT = os.path.join(os.path.dirname(SCRIPT_DIR), 'crossplay')
RESULTS_FILE = os.path.join(SCRIPT_DIR, 'ladder_results.txt')


def run_match(tier, opponent):
    """Run one match and return stdout."""
    env = os.environ.copy()
    env['PYTHONPATH'] = CROSSPLAY_ROOT
    env['PYTHONUNBUFFERED'] = '1'

    cmd = [
        sys.executable, '-u', 'play_match.py',
        'dadbot_v7', opponent,
        '--games', str(GAMES),
        '--seed', str(SEED),
        '--tier', tier,
    ]

    print(f"\n{'='*70}", flush=True)
    print(f"  {tier.upper()} TIER: DadBot-v7 vs {opponent} ({GAMES} games)", flush=True)
    print(f"{'='*70}", flush=True)

    t0 = time.time()
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=SCRIPT_DIR, env=env
    )
    elapsed = time.time() - t0

    output = result.stdout + result.stderr
    print(output, flush=True)

    return output, elapsed


def main():
    t_total = time.time()

    with open(RESULTS_FILE, 'w') as f:
        f.write(f"DadBot v7 Ladder — {GAMES} games each, seed {SEED}\n")
        f.write(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*70}\n\n")

    for tier in TIERS:
        tier_start = time.time()

        with open(RESULTS_FILE, 'a') as f:
            f.write(f"\n{'#'*70}\n")
            f.write(f"  {tier.upper()} TIER\n")
            f.write(f"{'#'*70}\n\n")

        for opponent in OPPONENTS:
            output, elapsed = run_match(tier, opponent)

            with open(RESULTS_FILE, 'a') as f:
                f.write(f"--- {opponent} ({elapsed:.0f}s) ---\n")
                # Extract just the results section
                in_results = False
                for line in output.split('\n'):
                    if 'Results:' in line or 'Speed Report' in line:
                        in_results = True
                    if in_results:
                        f.write(line + '\n')
                    if in_results and line.strip() == '':
                        in_results = False
                f.write('\n')

        tier_elapsed = time.time() - tier_start
        with open(RESULTS_FILE, 'a') as f:
            f.write(f"  {tier.upper()} tier total: {tier_elapsed/60:.0f} min\n\n")

    total = time.time() - t_total
    with open(RESULTS_FILE, 'a') as f:
        f.write(f"\n{'='*70}\n")
        f.write(f"Total time: {total/3600:.1f} hours\n")
        f.write(f"Finished: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    print(f"\n\nDone! Total time: {total/3600:.1f} hours", flush=True)
    print(f"Results saved to: {RESULTS_FILE}", flush=True)


if __name__ == '__main__':
    main()

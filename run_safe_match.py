"""Run v5 vs v7 match one game at a time in separate processes to survive MAGPIE crashes."""
import subprocess
import sys
import os
import re
import time
import argparse

PYTHON = sys.executable
WORK_DIR = os.path.dirname(os.path.abspath(__file__))


def run_one_game(engine1, engine2, seed, tier):
    """Run a single game in a subprocess, return parsed result or None on crash."""
    env = os.environ.copy()
    env['BOT_TIER'] = tier
    result = subprocess.run(
        [PYTHON, 'play_match.py', engine1, engine2, '--games', '1',
         '--tier', tier, '--seed', str(seed)],
        cwd=WORK_DIR, capture_output=True, text=True, env=env, timeout=120
    )
    if result.returncode != 0:
        return None, result.stderr.strip()

    # Parse output for wins/scores/timing
    out = result.stdout
    # Look for "Results:" block
    m_wins = re.search(r'(\w+) wins:\s+(\d+)\s+\|\s+(\w[\w-]*) wins:\s+(\d+)', out)
    m_spread = re.search(r'Avg spread:\s+([\+\-]?\d+\.?\d*)', out)
    m_scores = re.search(r'(\w+) avg:\s+([\d.]+)\s+\|\s+(\w[\w-]*) avg:\s+([\d.]+)', out)
    m_time1 = re.search(r'(DadBot):\s+avg ([\d.]+)s', out)
    m_time2 = re.search(r'(DadBot-v7):\s+avg ([\d.]+)s', out)

    if not m_wins:
        return None, "Could not parse output"

    e1_name = m_wins.group(1)
    e1_wins = int(m_wins.group(2))
    e2_name = m_wins.group(3)
    e2_wins = int(m_wins.group(4))
    spread = float(m_spread.group(1)) if m_spread else 0

    score1 = float(m_scores.group(2)) if m_scores else 0
    score2 = float(m_scores.group(4)) if m_scores else 0

    time1 = float(m_time1.group(2)) if m_time1 else 0
    time2 = float(m_time2.group(2)) if m_time2 else 0

    return {
        'e1_wins': e1_wins, 'e2_wins': e2_wins,
        'spread': spread, 'score1': score1, 'score2': score2,
        'time1': time1, 'time2': time2,
    }, None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('engine1', default='dadbot', nargs='?')
    parser.add_argument('engine2', default='dadbot_v7', nargs='?')
    parser.add_argument('--games', type=int, default=50)
    parser.add_argument('--tier', default='blitz')
    parser.add_argument('--seed', type=int, default=12345)
    args = parser.parse_args()

    import random
    rng = random.Random(args.seed)
    seeds = [rng.randint(0, 2**31) for _ in range(args.games)]

    e1_wins = e2_wins = ties = crashes = 0
    total_spread = 0
    total_score1 = total_score2 = 0.0
    times1, times2 = [], []
    crash_seeds = []
    t_start = time.time()

    print(f"\n{args.engine1} vs {args.engine2} ({args.games} games, tier={args.tier})")
    print(f"Master seed: {args.seed}")
    print(f"Running games in isolated subprocesses...\n")

    for i in range(args.games):
        # Alternate who goes first by using even/odd seed offset
        result, err = run_one_game(args.engine1, args.engine2, seeds[i], args.tier)

        if result is None:
            crashes += 1
            crash_seeds.append(seeds[i])
            tag = "CRASH"
            if err and 'Assertion' in err:
                tag = "MAGPIE CRASH"
            print(f"  [{i+1}/{args.games}] {tag} (seed={seeds[i]})")
            continue

        total_spread += result['spread']
        total_score1 += result['score1']
        total_score2 += result['score2']
        if result['time1'] > 0:
            times1.append(result['time1'])
        if result['time2'] > 0:
            times2.append(result['time2'])

        if result['e1_wins'] > result['e2_wins']:
            e1_wins += 1
        elif result['e2_wins'] > result['e1_wins']:
            e2_wins += 1
        else:
            ties += 1

        completed = e1_wins + e2_wins + ties
        elapsed = time.time() - t_start
        gps = completed / elapsed if elapsed > 0 else 0

        if (i + 1) % max(1, args.games // 10) == 0 or i + 1 == args.games:
            avg_sp = total_spread / completed if completed else 0
            print(f"  [{i+1}/{args.games}] {e1_wins}-{e2_wins}"
                  f" ({ties} ties, {crashes} crashes) spread: {avg_sp:+.1f}"
                  f" ({gps:.2f} games/s)")

    completed = e1_wins + e2_wins + ties
    elapsed = time.time() - t_start

    print(f"\n{'='*60}")
    print(f"  Results: {args.engine1} vs {args.engine2}")
    print(f"  Tier: {args.tier} | Games: {completed} completed, {crashes} crashed")
    print(f"{'='*60}")
    print(f"  {args.engine1} wins: {e1_wins:>4}  |  {args.engine2} wins: {e2_wins:>4}  |  Ties: {ties}")
    if completed > 0:
        print(f"  Avg spread:    {total_spread / completed:>+.1f}")
        print(f"  {args.engine1} avg: {total_score1 / completed:>6.1f}  |  {args.engine2} avg: {total_score2 / completed:>6.1f}")
    print(f"  Time: {elapsed:.1f}s ({completed / elapsed:.2f} games/s)")

    if times1:
        print(f"\n  Speed: {args.engine1} avg {sum(times1)/len(times1):.2f}s"
              f"  |  {args.engine2} avg {sum(times2)/len(times2):.2f}s")

    if crash_seeds:
        print(f"\n  Crash seeds ({len(crash_seeds)}): {crash_seeds[:10]}")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()

# Bot Versions

Each version is tagged in git. To test a version:
```
git checkout <tag>
python play_match.py my_bot defensive_bot --games 100
git checkout main
```

---

## v1-greedy
**Tag:** `v1-greedy`
**Strategy:** Pick highest-scoring move (greedy).
**Results:** Beats RandomBot ~100-0. Loses to smarter bots.

---

## v2-leave-eval
**Tag:** `v2-leave-eval`
**Strategy:** Greedy + leave evaluation (keep blanks=25, S=8, etc.).
**Results:** Beats GreedyBot ~55-45.

---

## v3-static-eval
**Tag:** `v3-static-eval`
**Strategy:** Leave eval + defensive penalties (-12 per 3W opened, -5 per 2W)
+ opponent modeling (scale defense when bag ≤ 7 and opponent likely has blanks/S).
**Results:** vs DefensiveBot: **50-50**, avg spread +10.9 (~3 min/100 games)

---

## v4-sim-20
**Tag:** `v4-sim-20`
**Strategy:** v3-static-eval + 1-ply Monte Carlo simulation (N_CANDIDATES=5, N_SAMPLES=20).
Opponent picks by score+leave, we record their raw score.
**Results:** vs DefensiveBot: **14-6 (70%)** over 20 games, avg spread +35 (~40 min/20 games)

---

## v5-greedy (current)
**Tag:** `v5-greedy`
**Strategy:** Pure greedy — always take the highest-scoring move. No leave eval, no defense.
**Results:** vs DefensiveBot: **51-49**, avg spread +5.2 (~2.5 min/100 games)

### 5-strategy comparison (all vs DefensiveBot, 100 games each)

| Strategy | Wins | Losses | Win% | Avg Spread | Avg Score |
|----------|------|--------|------|------------|-----------|
| Greedy (pure score) | 51 | 49 | **51%** | **+5.2** | 425.7 |
| BingoFisher (protect blanks) | 48 | 52 | 48% | -15.2 | 434.2 |
| SpreadAdaptive (adjust by gap) | 42 | 58 | 42% | -5.9 | 431.9 |
| StageBased (phases by bag size) | 34 | 66 | 34% | -34.8 | 420.6 |
| LeaveFirst (4x leave weight) | 28 | 72 | 28% | -59.3 | 394.4 |

**Takeaway:** Greedy wins. Against a defensive opponent, maximizing score
each turn is optimal. Complexity (leave eval, stage logic, spread adaptation)
all hurt performance. BingoFisher scores highest on average (434.2) but
still loses more games — holding blanks is costly.

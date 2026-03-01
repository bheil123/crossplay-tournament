$masterSeed = "700847761"
$resultsDir = "C:\Users\billh\crossplay-tournament\results"
$games = 20

Set-Location "C:\Users\billh\crossplay-tournament"

# All tests at N=30, K=400 (standard candidates, fast sims budget)
# This isolates heuristic effects without the ~10s/move overhead of full standard tier
$env:BOT_TIER = "standard"
$env:MC_WORKERS = "9"
$env:DADBOT_N = "30"
$env:DADBOT_K = "400"

# Clean slate: remove all heuristic overrides
function Clear-Overrides {
    Remove-Item Env:\DADBOT_NO_POSADJ -ErrorAction SilentlyContinue
    Remove-Item Env:\DADBOT_NO_BLANKCORR -ErrorAction SilentlyContinue
    Remove-Item Env:\DADBOT_NO_EXCHANGE -ErrorAction SilentlyContinue
    Remove-Item Env:\DADBOT_NO_BINGO -ErrorAction SilentlyContinue
    Remove-Item Env:\DADBOT_MYBOT_LEAVES -ErrorAction SilentlyContinue
    Remove-Item Env:\DADBOT_TIMING -ErrorAction SilentlyContinue
}

# ===================================================================
# Baseline: N=30, K=400, all heuristics ON (equivalent to v4 standard
# tier but with fast-speed sims)
# ===================================================================
Clear-Overrides
Write-Output "============================================================"
Write-Output "  BASELINE: N=30 K=400 all heuristics ON ($games games)"
Write-Output "============================================================"
python play_match.py dadbot my_bot --games $games --tier standard --seed $masterSeed 2>&1 | Tee-Object -FilePath "$resultsDir\regress_baseline_n30k400.txt"
Write-Output ""

# ===================================================================
# Test 1: MyBot leave formula (replace SuperLeaves + bingo with 26-char)
# PRIME SUSPECT: largest delta between DadBot and MyBot evaluation
# ===================================================================
Clear-Overrides
$env:DADBOT_MYBOT_LEAVES = "1"
Write-Output "============================================================"
Write-Output "  TEST 1: MYBOT LEAVES (N=30 K=400, $games games)"
Write-Output "============================================================"
python play_match.py dadbot my_bot --games $games --tier standard --seed $masterSeed 2>&1 | Tee-Object -FilePath "$resultsDir\regress_mybot_leaves.txt"
Write-Output ""

# ===================================================================
# Test 2: No positional adjustment (risk + DLS exposure disabled)
# ===================================================================
Clear-Overrides
$env:DADBOT_NO_POSADJ = "1"
Write-Output "============================================================"
Write-Output "  TEST 2: NO POSADJ (N=30 K=400, $games games)"
Write-Output "============================================================"
python play_match.py dadbot my_bot --games $games --tier standard --seed $masterSeed 2>&1 | Tee-Object -FilePath "$resultsDir\regress_no_posadj.txt"
Write-Output ""

# ===================================================================
# Test 3: No blank correction
# ===================================================================
Clear-Overrides
$env:DADBOT_NO_BLANKCORR = "1"
Write-Output "============================================================"
Write-Output "  TEST 3: NO BLANK CORRECTION (N=30 K=400, $games games)"
Write-Output "============================================================"
python play_match.py dadbot my_bot --games $games --tier standard --seed $masterSeed 2>&1 | Tee-Object -FilePath "$resultsDir\regress_no_blankcorr.txt"
Write-Output ""

# ===================================================================
# Test 4: No exchange evaluation
# ===================================================================
Clear-Overrides
$env:DADBOT_NO_EXCHANGE = "1"
Write-Output "============================================================"
Write-Output "  TEST 4: NO EXCHANGE (N=30 K=400, $games games)"
Write-Output "============================================================"
python play_match.py dadbot my_bot --games $games --tier standard --seed $masterSeed 2>&1 | Tee-Object -FilePath "$resultsDir\regress_no_exchange.txt"
Write-Output ""

# ===================================================================
# Test 5: No bingo bonus
# ===================================================================
Clear-Overrides
$env:DADBOT_NO_BINGO = "1"
Write-Output "============================================================"
Write-Output "  TEST 5: NO BINGO BONUS (N=30 K=400, $games games)"
Write-Output "============================================================"
python play_match.py dadbot my_bot --games $games --tier standard --seed $masterSeed 2>&1 | Tee-Object -FilePath "$resultsDir\regress_no_bingo.txt"
Write-Output ""

# ===================================================================
# Cleanup
# ===================================================================
Clear-Overrides
Remove-Item Env:\DADBOT_N -ErrorAction SilentlyContinue
Remove-Item Env:\DADBOT_K -ErrorAction SilentlyContinue
Write-Output "============================================================"
Write-Output "  Regression bisection complete!"
Write-Output "============================================================"

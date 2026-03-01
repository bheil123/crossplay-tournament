$masterSeed = "700847761"
$resultsDir = "C:\Users\billh\crossplay-tournament\results"
$games = 20

Set-Location "C:\Users\billh\crossplay-tournament"

# Clean all overrides
function Clear-Overrides {
    Remove-Item Env:\DADBOT_N -ErrorAction SilentlyContinue
    Remove-Item Env:\DADBOT_K -ErrorAction SilentlyContinue
    Remove-Item Env:\DADBOT_NO_POSADJ -ErrorAction SilentlyContinue
    Remove-Item Env:\DADBOT_NO_EXCHANGE -ErrorAction SilentlyContinue
    Remove-Item Env:\DADBOT_MYBOT_LEAVES -ErrorAction SilentlyContinue
    Remove-Item Env:\DADBOT_TIMING -ErrorAction SilentlyContinue
    Remove-Item Env:\DADBOT_DIAG_N -ErrorAction SilentlyContinue
}

$env:BOT_TIER = "fast"
$env:MC_WORKERS = "9"

# ===================================================================
# Baseline: N=30, K=400, new formula, posadj ON, exchange ON
# ===================================================================
Clear-Overrides
$env:DADBOT_N = "30"
$env:DADBOT_K = "400"
Write-Output "============================================================"
Write-Output "  BASELINE: N=30 K=400 formula + posadj + exchange ($games games)"
Write-Output "============================================================"
python play_match.py dadbot my_bot --games $games --tier fast --seed $masterSeed 2>&1 | Tee-Object -FilePath "$resultsDir\retest_baseline.txt"
Write-Output ""

# ===================================================================
# Test 1: No positional adjustment
# ===================================================================
Clear-Overrides
$env:DADBOT_N = "30"
$env:DADBOT_K = "400"
$env:DADBOT_NO_POSADJ = "1"
Write-Output "============================================================"
Write-Output "  NO POSADJ: N=30 K=400 ($games games)"
Write-Output "============================================================"
python play_match.py dadbot my_bot --games $games --tier fast --seed $masterSeed 2>&1 | Tee-Object -FilePath "$resultsDir\retest_no_posadj.txt"
Write-Output ""

# ===================================================================
# Test 2: No exchange evaluation
# ===================================================================
Clear-Overrides
$env:DADBOT_N = "30"
$env:DADBOT_K = "400"
$env:DADBOT_NO_EXCHANGE = "1"
Write-Output "============================================================"
Write-Output "  NO EXCHANGE: N=30 K=400 ($games games)"
Write-Output "============================================================"
python play_match.py dadbot my_bot --games $games --tier fast --seed $masterSeed 2>&1 | Tee-Object -FilePath "$resultsDir\retest_no_exchange.txt"
Write-Output ""

# ===================================================================
# Test 3: No posadj AND no exchange (pure MC + formula)
# ===================================================================
Clear-Overrides
$env:DADBOT_N = "30"
$env:DADBOT_K = "400"
$env:DADBOT_NO_POSADJ = "1"
$env:DADBOT_NO_EXCHANGE = "1"
Write-Output "============================================================"
Write-Output "  STRIPPED: N=30 K=400 pure MC + formula ($games games)"
Write-Output "============================================================"
python play_match.py dadbot my_bot --games $games --tier fast --seed $masterSeed 2>&1 | Tee-Object -FilePath "$resultsDir\retest_stripped.txt"
Write-Output ""

# ===================================================================
# Test 4: N=15 baseline (confirm fast tier still good)
# ===================================================================
Clear-Overrides
$env:DADBOT_N = "15"
$env:DADBOT_K = "400"
Write-Output "============================================================"
Write-Output "  N=15 BASELINE: K=400 formula + posadj + exchange ($games games)"
Write-Output "============================================================"
python play_match.py dadbot my_bot --games $games --tier fast --seed $masterSeed 2>&1 | Tee-Object -FilePath "$resultsDir\retest_n15_baseline.txt"
Write-Output ""

Clear-Overrides
Write-Output "============================================================"
Write-Output "  Heuristic retest complete!"
Write-Output "============================================================"

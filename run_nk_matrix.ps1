$masterSeed = "700847761"
$resultsDir = "C:\Users\billh\crossplay-tournament\results"
$games = 20

Set-Location "C:\Users\billh\crossplay-tournament"

# Clean all overrides
Remove-Item Env:\DADBOT_NO_POSADJ -ErrorAction SilentlyContinue
Remove-Item Env:\DADBOT_NO_EXCHANGE -ErrorAction SilentlyContinue
Remove-Item Env:\DADBOT_MYBOT_LEAVES -ErrorAction SilentlyContinue
Remove-Item Env:\DADBOT_TIMING -ErrorAction SilentlyContinue

$env:BOT_TIER = "fast"
$env:MC_WORKERS = "9"

# We already have:
#   N=30, K=1500 -> 12-8  (run_standard_fixed.ps1)
# Need the other 3 cells of the 2x2 matrix:

# Cell 1: N=15, K=400 (fast tier baseline with fixed code)
$env:DADBOT_N = "15"
$env:DADBOT_K = "400"
Write-Output "============================================================"
Write-Output "  N=15 K=400 (fast baseline, fixed code) $games games"
Write-Output "============================================================"
python play_match.py dadbot my_bot --games $games --tier fast --seed $masterSeed 2>&1 | Tee-Object -FilePath "$resultsDir\nk_n15_k400.txt"
Write-Output ""

# Cell 2: N=30, K=400 (more candidates, fast sims)
$env:DADBOT_N = "30"
$env:DADBOT_K = "400"
Write-Output "============================================================"
Write-Output "  N=30 K=400 (more candidates, fast sims) $games games"
Write-Output "============================================================"
python play_match.py dadbot my_bot --games $games --tier fast --seed $masterSeed 2>&1 | Tee-Object -FilePath "$resultsDir\nk_n30_k400.txt"
Write-Output ""

# Cell 3: N=15, K=1500 (few candidates, deep sims)
$env:DADBOT_N = "15"
$env:DADBOT_K = "1500"
Write-Output "============================================================"
Write-Output "  N=15 K=1500 (few candidates, deep sims) $games games"
Write-Output "============================================================"
python play_match.py dadbot my_bot --games $games --tier fast --seed $masterSeed 2>&1 | Tee-Object -FilePath "$resultsDir\nk_n15_k1500.txt"
Write-Output ""

Remove-Item Env:\DADBOT_N -ErrorAction SilentlyContinue
Remove-Item Env:\DADBOT_K -ErrorAction SilentlyContinue

Write-Output "============================================================"
Write-Output "  N vs K matrix complete!"
Write-Output "============================================================"

$masterSeed = "700847761"
$resultsDir = "C:\Users\billh\crossplay-tournament\results"

Set-Location "C:\Users\billh\crossplay-tournament"

# Clean all overrides
Remove-Item Env:\DADBOT_NO_POSADJ -ErrorAction SilentlyContinue
Remove-Item Env:\DADBOT_NO_EXCHANGE -ErrorAction SilentlyContinue
Remove-Item Env:\DADBOT_MYBOT_LEAVES -ErrorAction SilentlyContinue
Remove-Item Env:\DADBOT_TIMING -ErrorAction SilentlyContinue

$env:BOT_TIER = "fast"
$env:MC_WORKERS = "9"
$env:DADBOT_N = "30"
$env:DADBOT_K = "400"
$env:DADBOT_DIAG_N = "1"

Write-Output "============================================================"
Write-Output "  N-BUG DIAGNOSTIC: N=30 K=400, 5 games"
Write-Output "============================================================"

python play_match.py dadbot my_bot --games 5 --tier fast --seed $masterSeed 2>&1 | Tee-Object -FilePath "$resultsDir\ndiag_n30.txt"

Remove-Item Env:\DADBOT_N -ErrorAction SilentlyContinue
Remove-Item Env:\DADBOT_K -ErrorAction SilentlyContinue
Remove-Item Env:\DADBOT_DIAG_N -ErrorAction SilentlyContinue

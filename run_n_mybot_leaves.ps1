$masterSeed = "700847761"
$resultsDir = "C:\Users\billh\crossplay-tournament\results"

Set-Location "C:\Users\billh\crossplay-tournament"

Remove-Item Env:\DADBOT_NO_POSADJ -ErrorAction SilentlyContinue
Remove-Item Env:\DADBOT_NO_EXCHANGE -ErrorAction SilentlyContinue
Remove-Item Env:\DADBOT_TIMING -ErrorAction SilentlyContinue
Remove-Item Env:\DADBOT_DIAG_N -ErrorAction SilentlyContinue

$env:BOT_TIER = "fast"
$env:MC_WORKERS = "9"
$env:DADBOT_MYBOT_LEAVES = "1"

# N=15 with MyBot leaves (baseline)
$env:DADBOT_N = "15"
$env:DADBOT_K = "400"
Write-Output "============================================================"
Write-Output "  MYBOT LEAVES N=15 K=400 (20 games)"
Write-Output "============================================================"
python play_match.py dadbot my_bot --games 20 --tier fast --seed $masterSeed 2>&1 | Tee-Object -FilePath "$resultsDir\mybot_lv_n15_k400.txt"
Write-Output ""

# N=30 with MyBot leaves (does N-scaling still hurt?)
$env:DADBOT_N = "30"
$env:DADBOT_K = "400"
Write-Output "============================================================"
Write-Output "  MYBOT LEAVES N=30 K=400 (20 games)"
Write-Output "============================================================"
python play_match.py dadbot my_bot --games 20 --tier fast --seed $masterSeed 2>&1 | Tee-Object -FilePath "$resultsDir\mybot_lv_n30_k400.txt"
Write-Output ""

Remove-Item Env:\DADBOT_N -ErrorAction SilentlyContinue
Remove-Item Env:\DADBOT_K -ErrorAction SilentlyContinue
Remove-Item Env:\DADBOT_MYBOT_LEAVES -ErrorAction SilentlyContinue

Write-Output "MyBot leaves N-scaling test complete!"

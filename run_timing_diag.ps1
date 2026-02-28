$env:BOT_TIER = "standard"
$env:MC_WORKERS = "7"
$env:DADBOT_TIMING = "1"
Set-Location "C:\Users\billh\crossplay-tournament"

Write-Output "=== DadBot v4 Timing Diagnostics ==="
Write-Output "Standard tier, 3 games, same seeds"
Write-Output ""

python play_match.py dadbot my_bot --games 3 --tier standard --game-seeds 743081093,725414342,1915759923 2>&1 | Tee-Object -FilePath "C:\Users\billh\crossplay-tournament\results\v4_timing_diag.txt"

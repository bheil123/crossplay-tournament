$env:BOT_TIER = "standard"
$env:DADBOT_TIMING = "1"
Set-Location "C:\Users\billh\crossplay-tournament"

Write-Output "=== DadBot v4 Final Smoke Test ==="
Write-Output "Standard tier, 9 workers (default), same seeds"
Write-Output "Expected: 3-0, spread ~+105"
Write-Output ""

python play_match.py dadbot my_bot --games 3 --tier standard --game-seeds 743081093,725414342,1915759923 2>&1 | Tee-Object -FilePath "C:\Users\billh\crossplay-tournament\results\v4_final_smoke.txt"

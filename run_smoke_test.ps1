$env:BOT_TIER = "standard"
$env:MC_WORKERS = "7"
Set-Location "C:\Users\billh\crossplay-tournament"

Write-Output "=== DadBot v4 Smoke Test ==="
Write-Output "Same seeds as bisection baseline: 743081093,725414342,1915759923"
Write-Output "Expected: 3-0, spread ~+107"
Write-Output ""

python play_match.py dadbot my_bot --games 3 --tier standard --game-seeds 743081093,725414342,1915759923 2>&1 | Tee-Object -FilePath "C:\Users\billh\crossplay-tournament\results\v4_smoke_test.txt"

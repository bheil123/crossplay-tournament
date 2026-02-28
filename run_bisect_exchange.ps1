# Test: exchange screening OFF (EXCHANGE_EVAL=False)
# Same seeds as original bisection for comparability
$env:BOT_TIER = "standard"
$env:MC_WORKERS = "7"
$env:DADBOT_OVERRIDE_EXCHANGE_EVAL = "false"
Set-Location "C:\Users\billh\crossplay-tournament"
python play_match.py dadbot my_bot --games 3 --tier standard --game-seeds 743081093,725414342,1915759923 2>&1 | Tee-Object -FilePath "C:\Users\billh\crossplay-tournament\results\bisect_exchange_off.txt"

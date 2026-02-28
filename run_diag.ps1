$env:BOT_TIER = "standard"
$env:MC_WORKERS = "3"
Set-Location "C:\Users\billh\crossplay-tournament"
python play_match.py dadbot my_bot --games 3 --tier standard --game-seeds 743081093,725414342,1915759923 2>&1 | Tee-Object -FilePath "C:\Users\billh\crossplay-tournament\results\blank3ply_exchange_diag.txt"

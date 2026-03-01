$masterSeed = "700847761"
$resultsDir = "C:\Users\billh\crossplay-tournament\results"

Set-Location "C:\Users\billh\crossplay-tournament"

# Clean all overrides
Remove-Item Env:\DADBOT_N -ErrorAction SilentlyContinue
Remove-Item Env:\DADBOT_K -ErrorAction SilentlyContinue
Remove-Item Env:\DADBOT_NO_POSADJ -ErrorAction SilentlyContinue
Remove-Item Env:\DADBOT_NO_EXCHANGE -ErrorAction SilentlyContinue
Remove-Item Env:\DADBOT_MYBOT_LEAVES -ErrorAction SilentlyContinue
Remove-Item Env:\DADBOT_TIMING -ErrorAction SilentlyContinue

$env:BOT_TIER = "standard"
$env:MC_WORKERS = "9"

Write-Output "============================================================"
Write-Output "  FIXED DadBot vs MyBot: standard tier (20 games)"
Write-Output "  Removed: bingo bonus, blank correction"
Write-Output "============================================================"

python play_match.py dadbot my_bot --games 20 --tier standard --seed $masterSeed 2>&1 | Tee-Object -FilePath "$resultsDir\fixed_standard_v4.txt"

Write-Output ""
Write-Output "Standard tier fixed test complete!"

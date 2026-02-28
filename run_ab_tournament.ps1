$env:BOT_TIER = "standard"
$resultsDir = "C:\Users\billh\crossplay-tournament\results"
$masterSeed = "700847761"

Set-Location "C:\Users\billh\crossplay-tournament"

Write-Output "============================================================"
Write-Output "  A/B Tournament: DadBot v3 vs MyBot (20 games, standard)"
Write-Output "============================================================"
# v3 uses its own default workers (cpu_count - 5 = 7)
$env:MC_WORKERS = "7"
Remove-Item Env:\DADBOT_TIMING -ErrorAction SilentlyContinue

python play_match.py dadbot_v3 my_bot --games 20 --tier standard --seed $masterSeed 2>&1 | Tee-Object -FilePath "$resultsDir\ab_v3_vs_mybot.txt"
Write-Output ""

Write-Output "============================================================"
Write-Output "  A/B Tournament: DadBot v4 vs MyBot (20 games, standard)"
Write-Output "============================================================"
# v4 uses new default workers (cpu_count - 3 = 9)
$env:MC_WORKERS = "9"
Remove-Item Env:\DADBOT_TIMING -ErrorAction SilentlyContinue

python play_match.py dadbot my_bot --games 20 --tier standard --seed $masterSeed 2>&1 | Tee-Object -FilePath "$resultsDir\ab_v4_vs_mybot.txt"
Write-Output ""

Write-Output "A/B Tournament complete!"

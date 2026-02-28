$env:BOT_TIER = "standard"
$env:DADBOT_TIMING = "1"
$seeds = "743081093,725414342,1915759923"
$resultsDir = "C:\Users\billh\crossplay-tournament\results"

Set-Location "C:\Users\billh\crossplay-tournament"

foreach ($w in @(5, 7, 9)) {
    Write-Output "=============================================="
    Write-Output "  Testing with $w MC workers"
    Write-Output "=============================================="
    $env:MC_WORKERS = "$w"

    python play_match.py dadbot my_bot --games 3 --tier standard --game-seeds $seeds 2>&1 | Tee-Object -FilePath "$resultsDir\workers_$w.txt"
    Write-Output ""
}

Write-Output "Worker sweep complete!"

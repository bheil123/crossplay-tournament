$env:DADBOT_TIMING = "1"
$seeds = "743081093"
$resultsDir = "C:\Users\billh\crossplay-tournament\results"

Set-Location "C:\Users\billh\crossplay-tournament"

foreach ($tier in @("fast", "deep")) {
    Write-Output "=============================================="
    Write-Output "  Tier: $tier (tuned, 1 game)"
    Write-Output "=============================================="
    $env:BOT_TIER = $tier

    python play_match.py dadbot my_bot --games 1 --tier $tier --game-seeds $seeds 2>&1 | Tee-Object -FilePath "$resultsDir\tier_${tier}_tuned.txt"
    Write-Output ""
}

Write-Output "Tuned tier tests complete!"

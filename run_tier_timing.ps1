$env:DADBOT_TIMING = "1"
$seeds = "743081093"
$resultsDir = "C:\Users\billh\crossplay-tournament\results"

Set-Location "C:\Users\billh\crossplay-tournament"

foreach ($tier in @("blitz", "fast", "standard", "deep")) {
    Write-Output "=============================================="
    Write-Output "  Tier: $tier (1 game baseline)"
    Write-Output "=============================================="
    $env:BOT_TIER = $tier

    python play_match.py dadbot my_bot --games 1 --tier $tier --game-seeds $seeds 2>&1 | Tee-Object -FilePath "$resultsDir\tier_${tier}_baseline.txt"
    Write-Output ""
}

Write-Output "Tier timing baseline complete!"

$masterSeed = "700847761"
$resultsDir = "C:\Users\billh\crossplay-tournament\results"

Set-Location "C:\Users\billh\crossplay-tournament"

foreach ($tier in @("blitz", "fast", "deep")) {
    if ($tier -eq "deep") { $games = 10 } else { $games = 20 }

    # --- v3 (7 workers, its original default) ---
    Write-Output "============================================================"
    Write-Output "  DadBot v3 vs MyBot: $tier tier ($games games)"
    Write-Output "============================================================"
    $env:BOT_TIER = $tier
    $env:MC_WORKERS = "7"
    Remove-Item Env:\DADBOT_TIMING -ErrorAction SilentlyContinue

    python play_match.py dadbot_v3 my_bot --games $games --tier $tier --seed $masterSeed 2>&1 | Tee-Object -FilePath "$resultsDir\ab_${tier}_v3_vs_mybot.txt"
    Write-Output ""

    # --- v4 (9 workers, new default) ---
    Write-Output "============================================================"
    Write-Output "  DadBot v4 vs MyBot: $tier tier ($games games)"
    Write-Output "============================================================"
    $env:MC_WORKERS = "9"
    Remove-Item Env:\DADBOT_TIMING -ErrorAction SilentlyContinue

    python play_match.py dadbot my_bot --games $games --tier $tier --seed $masterSeed 2>&1 | Tee-Object -FilePath "$resultsDir\ab_${tier}_v4_vs_mybot.txt"
    Write-Output ""
}

Write-Output "Multi-tier A/B Tournament complete!"

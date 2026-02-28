$env:BOT_TIER = "standard"
$env:MC_WORKERS = "7"
$seeds = "743081093,725414342,1915759923"
$resultsDir = "C:\Users\billh\crossplay-tournament\results"

$heuristics = @("risk", "blocking", "dls", "dd", "turnover", "hvt")

foreach ($h in $heuristics) {
    Write-Output "=============================================="
    Write-Output "  Testing with $h DISABLED"
    Write-Output "=============================================="
    $env:DADBOT_DISABLE_HEURISTIC = $h
    # Clear any override flags
    Remove-Item Env:\DADBOT_OVERRIDE_POSITIONAL_ADJ -ErrorAction SilentlyContinue
    Remove-Item Env:\DADBOT_OVERRIDE_EXCHANGE_EVAL -ErrorAction SilentlyContinue

    Set-Location "C:\Users\billh\crossplay-tournament"
    python play_match.py dadbot my_bot --games 3 --tier standard --game-seeds $seeds 2>&1 | Tee-Object -FilePath "$resultsDir\bisect_no_$h.txt"
    Write-Output ""
}

# Clear the disable flag
Remove-Item Env:\DADBOT_DISABLE_HEURISTIC -ErrorAction SilentlyContinue
Write-Output "All heuristic bisection tests complete!"

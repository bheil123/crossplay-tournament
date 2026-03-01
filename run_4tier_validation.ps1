$masterSeed = "700847761"
$resultsDir = "C:\Users\billh\crossplay-tournament\results"
$games = 20

Set-Location "C:\Users\billh\crossplay-tournament"

# Clean all overrides
Remove-Item Env:\DADBOT_N -ErrorAction SilentlyContinue
Remove-Item Env:\DADBOT_K -ErrorAction SilentlyContinue
Remove-Item Env:\DADBOT_NO_POSADJ -ErrorAction SilentlyContinue
Remove-Item Env:\DADBOT_NO_EXCHANGE -ErrorAction SilentlyContinue
Remove-Item Env:\DADBOT_MYBOT_LEAVES -ErrorAction SilentlyContinue
Remove-Item Env:\DADBOT_TIMING -ErrorAction SilentlyContinue
Remove-Item Env:\DADBOT_DIAG_N -ErrorAction SilentlyContinue

$env:MC_WORKERS = "9"

# ===================================================================
# DadBot v5 -- 4-tier validation
# Pure MC 2-ply + MyBot leave formula (no posadj, no exchange, no bingo)
# ===================================================================

# Tier 1: Blitz (N=7, K=150)
$env:BOT_TIER = "blitz"
Write-Output "============================================================"
Write-Output "  BLITZ: N=7 K=150 ($games games)"
Write-Output "============================================================"
python play_match.py dadbot my_bot --games $games --tier blitz --seed $masterSeed 2>&1 | Tee-Object -FilePath "$resultsDir\v5_blitz.txt"
Write-Output ""

# Tier 2: Fast (N=15, K=400)
$env:BOT_TIER = "fast"
Write-Output "============================================================"
Write-Output "  FAST: N=15 K=400 ($games games)"
Write-Output "============================================================"
python play_match.py dadbot my_bot --games $games --tier fast --seed $masterSeed 2>&1 | Tee-Object -FilePath "$resultsDir\v5_fast.txt"
Write-Output ""

# Tier 3: Standard (N=30, K=1500)
$env:BOT_TIER = "standard"
Write-Output "============================================================"
Write-Output "  STANDARD: N=30 K=1500 ($games games)"
Write-Output "============================================================"
python play_match.py dadbot my_bot --games $games --tier standard --seed $masterSeed 2>&1 | Tee-Object -FilePath "$resultsDir\v5_standard.txt"
Write-Output ""

# Tier 4: Deep (N=35, K=2000)
$env:BOT_TIER = "deep"
Write-Output "============================================================"
Write-Output "  DEEP: N=35 K=2000 ($games games)"
Write-Output "============================================================"
python play_match.py dadbot my_bot --games $games --tier deep --seed $masterSeed 2>&1 | Tee-Object -FilePath "$resultsDir\v5_deep.txt"
Write-Output ""

Write-Output "============================================================"
Write-Output "  DadBot v5 4-tier validation complete!"
Write-Output "============================================================"

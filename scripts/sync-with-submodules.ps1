# PowerShell script: Sync main repository and submodules
# Usage: .\scripts\sync-with-submodules.ps1

Write-Host "Syncing main repository and submodules..." -ForegroundColor Cyan

# 1. Pull main repository updates
Write-Host ""
Write-Host "[1/3] Pulling main repository updates..." -ForegroundColor Yellow
git pull

# 2. Initialize and update all submodules
Write-Host ""
Write-Host "[2/3] Updating submodules..." -ForegroundColor Yellow
git submodule update --init --recursive

# 3. Show submodule status
Write-Host ""
Write-Host "[3/3] Submodule status:" -ForegroundColor Yellow
git submodule status

Write-Host ""
Write-Host "Sync completed!" -ForegroundColor Green

# Switch to the DeepWin directory
Set-Location -Path ".\DeepWin\src"

# Activate the conda environment
conda activate deepwin

# Display the current directory and environment information
Write-Host "Current directory: $(Get-Location)"
Write-Host "Current conda environment: deepwin" 
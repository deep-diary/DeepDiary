# Switch to the DeepWin directory
Set-Location -Path ".\DeepWin"

# Activate the conda environment
conda activate DiaryWin

# Display the current directory and environment information
Write-Host "Current directory: $(Get-Location)"
Write-Host "Current conda environment: DiaryWin" 
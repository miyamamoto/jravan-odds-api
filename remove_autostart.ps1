# JRA-VAN Odds API Server - Remove Auto-start Script

#Requires -RunAsAdministrator

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Remove Auto-start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$TaskName = "JRA-VAN-Odds-API-Server"

# Check if task exists
$Task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if (-not $Task) {
    Write-Host "INFO: Task '$TaskName' does not exist." -ForegroundColor Yellow
    Write-Host "Nothing to remove." -ForegroundColor Yellow
    exit 0
}

# Confirm removal
Write-Host "WARNING: This will completely remove the auto-start task." -ForegroundColor Yellow
Write-Host "You will need to run setup_autostart.ps1 again to re-enable it." -ForegroundColor Yellow
Write-Host ""
$response = Read-Host "Are you sure you want to remove the task? (y/n)"

if ($response -ne 'y') {
    Write-Host "Removal cancelled." -ForegroundColor Yellow
    exit 0
}

# Remove the task
try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host ""
    Write-Host "SUCCESS: Auto-start task removed." -ForegroundColor Green
    Write-Host "The API server will NOT start automatically on system startup." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To re-enable, run: .\setup_autostart.ps1" -ForegroundColor Cyan
} catch {
    Write-Host ""
    Write-Host "ERROR: Failed to remove task" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

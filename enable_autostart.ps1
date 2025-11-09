# JRA-VAN Odds API Server - Enable Auto-start Script

#Requires -RunAsAdministrator

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Enable Auto-start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$TaskName = "JRA-VAN-Odds-API-Server"

# Check if task exists
$Task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if (-not $Task) {
    Write-Host "ERROR: Task '$TaskName' does not exist." -ForegroundColor Red
    Write-Host "Run .\setup_autostart.ps1 first to create the task." -ForegroundColor Yellow
    exit 1
}

# Enable the task
try {
    Enable-ScheduledTask -TaskName $TaskName | Out-Null
    Write-Host "SUCCESS: Auto-start enabled." -ForegroundColor Green
    Write-Host "The API server will start automatically on system startup." -ForegroundColor Green
    Write-Host ""
    Write-Host "To disable, run: .\disable_autostart.ps1" -ForegroundColor Cyan
} catch {
    Write-Host "ERROR: Failed to enable task" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

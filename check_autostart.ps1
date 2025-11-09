# JRA-VAN Odds API Server - Check Auto-start Status

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Auto-start Status" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$TaskName = "JRA-VAN-Odds-API-Server"

# Check if task exists
$Task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if (-not $Task) {
    Write-Host "Status: NOT CONFIGURED" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "The auto-start task has not been set up." -ForegroundColor Yellow
    Write-Host "Run .\setup_autostart.ps1 to configure auto-start." -ForegroundColor Cyan
    exit 0
}

# Get task info
$TaskInfo = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction SilentlyContinue

# Display status
Write-Host "Task Name: $($Task.TaskName)" -ForegroundColor White
Write-Host "State: " -NoNewline

if ($Task.State -eq "Ready") {
    Write-Host "ENABLED" -ForegroundColor Green
} elseif ($Task.State -eq "Disabled") {
    Write-Host "DISABLED" -ForegroundColor Yellow
} else {
    Write-Host $Task.State -ForegroundColor White
}

Write-Host ""
Write-Host "Details:" -ForegroundColor Cyan
Write-Host "  Description: $($Task.Description)"
Write-Host "  User: $($Task.Principal.UserId)"
Write-Host "  Trigger: $($Task.Triggers[0].GetType().Name -replace 'Trigger$', '')"

if ($TaskInfo) {
    Write-Host "  Last Run Time: $($TaskInfo.LastRunTime)"
    Write-Host "  Last Result: " -NoNewline
    if ($TaskInfo.LastTaskResult -eq 0) {
        Write-Host "Success (0)" -ForegroundColor Green
    } else {
        Write-Host "$($TaskInfo.LastTaskResult)" -ForegroundColor Red
    }
    Write-Host "  Next Run Time: $($TaskInfo.NextRunTime)"
}

Write-Host ""
Write-Host "Action:" -ForegroundColor Cyan
Write-Host "  Execute: $($Task.Actions[0].Execute)"
Write-Host "  Working Directory: $($Task.Actions[0].WorkingDirectory)"

Write-Host ""
Write-Host "Management Commands:" -ForegroundColor Yellow
if ($Task.State -eq "Ready") {
    Write-Host "  Disable: .\disable_autostart.ps1"
    Write-Host "  Remove:  .\remove_autostart.ps1"
} elseif ($Task.State -eq "Disabled") {
    Write-Host "  Enable:  .\enable_autostart.ps1"
    Write-Host "  Remove:  .\remove_autostart.ps1"
}
Write-Host "  Test Run: Start-ScheduledTask -TaskName '$TaskName'"
Write-Host ""

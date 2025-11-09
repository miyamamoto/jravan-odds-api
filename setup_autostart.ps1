# JRA-VAN Odds API Server - Auto-start Setup Script
# This script registers the API server to start automatically on Windows startup

# Requires Administrator privileges
#Requires -RunAsAdministrator

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "JRA-VAN Odds API Server" -ForegroundColor Cyan
Write-Host "Auto-start Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BatchFile = Join-Path $ScriptDir "start_server.bat"

# Task name
$TaskName = "JRA-VAN-Odds-API-Server"

# Check if batch file exists
if (-not (Test-Path $BatchFile)) {
    Write-Host "ERROR: start_server.bat not found at: $BatchFile" -ForegroundColor Red
    Write-Host "Please ensure the batch file exists in the same directory." -ForegroundColor Red
    exit 1
}

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Task Name: $TaskName"
Write-Host "  Script Location: $BatchFile"
Write-Host "  Current User: $env:USERNAME"
Write-Host ""

# Check if task already exists
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($ExistingTask) {
    Write-Host "WARNING: Task '$TaskName' already exists." -ForegroundColor Yellow
    $response = Read-Host "Do you want to replace it? (y/n)"

    if ($response -ne 'y') {
        Write-Host "Setup cancelled." -ForegroundColor Yellow
        exit 0
    }

    Write-Host "Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Existing task removed." -ForegroundColor Green
}

# Create task action (what to run)
Write-Host "Creating task action..." -ForegroundColor Cyan
$Action = New-ScheduledTaskAction -Execute $BatchFile -WorkingDirectory $ScriptDir

# Create task trigger (when to run)
Write-Host "Creating task trigger (at startup)..." -ForegroundColor Cyan
$Trigger = New-ScheduledTaskTrigger -AtStartup

# Create task settings
Write-Host "Creating task settings..." -ForegroundColor Cyan
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

# Create task principal (run as current user)
Write-Host "Creating task principal..." -ForegroundColor Cyan
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

# Register the task
Write-Host "Registering scheduled task..." -ForegroundColor Cyan
try {
    $Task = Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Principal $Principal `
        -Description "Automatically starts JRA-VAN Odds API Server on system startup"

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "SUCCESS: Auto-start configured!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:" -ForegroundColor Yellow
    Write-Host "  Name: $($Task.TaskName)"
    Write-Host "  State: $($Task.State)"
    Write-Host "  Trigger: At system startup"
    Write-Host "  Action: $BatchFile"
    Write-Host ""
    Write-Host "The API server will now start automatically when Windows boots." -ForegroundColor Green
    Write-Host ""
    Write-Host "Management Commands:" -ForegroundColor Yellow
    Write-Host "  Enable:  .\enable_autostart.ps1"
    Write-Host "  Disable: .\disable_autostart.ps1"
    Write-Host "  Remove:  .\remove_autostart.ps1"
    Write-Host "  Status:  .\check_autostart.ps1"
    Write-Host ""

} catch {
    Write-Host ""
    Write-Host "ERROR: Failed to register task" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Ask if user wants to test the task
Write-Host "Would you like to test the task by starting it now? (y/n): " -NoNewline -ForegroundColor Yellow
$testResponse = Read-Host

if ($testResponse -eq 'y') {
    Write-Host ""
    Write-Host "Starting task..." -ForegroundColor Cyan
    Start-ScheduledTask -TaskName $TaskName
    Write-Host "Task started. Check the logs folder for output." -ForegroundColor Green
    Write-Host ""
}

Write-Host "Setup complete!" -ForegroundColor Green

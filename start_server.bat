@echo off
REM JRA-VAN Odds API Server Startup Script
REM This script starts the API server with logging

echo ========================================
echo JRA-VAN Odds API Server
echo Starting at %date% %time%
echo ========================================

REM Change to script directory
cd /d %~dp0

REM Create logs directory if not exists
if not exist "logs" mkdir logs

REM Set log file with timestamp
set LOGFILE=logs\server_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log
set LOGFILE=%LOGFILE: =0%

echo Log file: %LOGFILE%
echo.

REM Start the server and redirect output to log file
python run.py >> "%LOGFILE%" 2>&1

REM If server crashes, wait before exiting
if errorlevel 1 (
    echo.
    echo ERROR: Server exited with error code %errorlevel%
    echo Check log file: %LOGFILE%
    timeout /t 30
)

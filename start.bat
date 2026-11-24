@echo off
setlocal
cd /d "%~dp0"
if exist "%~dp0DM-Migration-1.0.2.exe" (
    start "" "%~dp0DM-Migration-1.0.2.exe"
    exit /b 0
)
if exist "%~dp0DM-Migration-1.0.2-standalone.exe" (
    start "" "%~dp0DM-Migration-1.0.2-standalone.exe"
    exit /b 0
)
if exist "%~dp0DM-Migration-1.0.1.exe" (
    start "" "%~dp0DM-Migration-1.0.1.exe"
    exit /b 0
)
if exist "%~dp0DM-Migration-1.0.0.exe" (
    start "" "%~dp0DM-Migration-1.0.0.exe"
    exit /b 0
)
if exist "%~dp0DM-Migration.exe" (
    start "" "%~dp0DM-Migration.exe"
    exit /b 0
)
where python >nul 2>nul
if errorlevel 1 (
    echo Python 3.10+ is required. Install Python or use a packaged DM-Migration EXE.
    pause
    exit /b 1
)
python -X utf8 "%~dp0app.py"
if errorlevel 1 pause

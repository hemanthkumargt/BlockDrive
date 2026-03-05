@echo off
echo ============================================
echo   BlockDrive - Join as Storage Node
echo ============================================
echo.
echo This script connects THIS laptop to the BlockDrive
echo network as a Storage Node.
echo.

:: Ask for the Hub IP
set /p HUB_IP="Enter the Hub IP address (shown on the host machine): "

if "%HUB_IP%"=="" (
    echo [ERROR] No IP entered. Exiting.
    pause
    exit /b 1
)

set HUB_URL=http://%HUB_IP%:8000

echo.
echo [*] Connecting to Hub at: %HUB_URL%
echo [*] Starting Storage Node...
echo.
echo ============================================
echo  Once connected, you will appear on the
echo  BlockDrive dashboard at:
echo  http://%HUB_IP%:8501
echo ============================================
echo.

:: Run from the secure-storage-main folder
cd /d "%~dp0"
python smart_node.py "" "%HUB_URL%"

pause

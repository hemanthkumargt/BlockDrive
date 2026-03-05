@echo off
echo ============================================
echo   BlockDrive - Local Network Launcher
echo ============================================
echo.

:: Get local IP address
for /f "tokens=4 delims= " %%a in ('route print 0.0.0.0 ^| findstr /r "0\.0\.0\.0"') do (
    set LOCAL_IP=%%a
    goto :found
)
:found

echo [*] Your Local Network IP: %LOCAL_IP%
echo.
echo [*] Starting FastAPI Backend on port 8000...
start "BlockDrive - Backend" cmd /k "cd /d "%~dp0" && python -m uvicorn backend:app --host 0.0.0.0 --port 8000"

echo [*] Waiting for backend to start...
timeout /t 3 /nobreak > nul

echo [*] Starting Streamlit Frontend on port 8501...
start "BlockDrive - Frontend" cmd /k "cd /d "%~dp0" && set BACKEND_URL=http://%LOCAL_IP%:8000 && streamlit run frontend.py --server.port 8501 --server.address 0.0.0.0"

echo.
echo ============================================
echo   BlockDrive HUB is RUNNING!
echo ============================================
echo.
echo   [YOUR MACHINE]  : http://localhost:8501
echo   [OTHER DEVICES] : http://%LOCAL_IP%:8501
echo.
echo   Backend API     : http://%LOCAL_IP%:8000
echo.
echo ============================================
echo   HOW TO ADD MORE DEVICES (up to 5 nodes):
echo ============================================
echo.
echo   On each OTHER laptop/device on same WiFi:
echo   1. Copy the "secure-storage-main" folder
echo   2. Install: pip install requests cryptography
echo   3. Double-click "join_network.bat"
echo   4. Enter this Hub IP when asked: %LOCAL_IP%
echo.
echo   They will appear on the dashboard instantly!
echo ============================================
echo.
pause

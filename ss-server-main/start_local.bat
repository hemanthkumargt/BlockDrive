@echo off
setlocal
echo ============================================
echo   BlockDrive - Simple Launcher
echo ============================================
echo.

:: Get local IP address
for /f "tokens=4 delims= " %%a in ('route print 0.0.0.0 ^| findstr /r "0\.0\.0\.0"') do (
    set "LOCAL_IP=%%a"
    goto :found
)
:found
set "LOCAL_IP=%LOCAL_IP: =%"

echo [*] Hub IP Address: %LOCAL_IP%
echo.

:: 1. Start Hub (Clean)
echo [*] Starting Backend...
start "BlockDrive-Hub" /min cmd /c "cd /d %~dp0 && python -m uvicorn backend:app --host 0.0.0.0 --port 8000 --log-level warning"

:: 2. Start Local Storage Node (Hidden)
timeout /t 1 /nobreak > nul
echo [*] Adding Local Node...
start "BlockDrive-Node" /min cmd /c "cd /d %~dp0 && cd ..\secure-storage-main && python smart_node.py Host-Node http://localhost:8000"

:: 3. Start UI and Browser
timeout /t 1 /nobreak > nul
echo [*] Launching Dashboard...
echo.
echo ============================================
echo   DONE! Opening http://localhost:8501 now.
echo ============================================
echo.
start "BlockDrive-UI" cmd /c "cd /d %~dp0 && set BACKEND_URL=http://%LOCAL_IP%:8000 && streamlit run frontend.py --server.port 8501 --server.address 0.0.0.0 --browser.serverAddress localhost"

timeout /t 5 > nul
exit

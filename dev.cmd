@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Brak srodowiska .venv.
    echo Uruchom najpierw: py -m venv .venv
    exit /b 1
)

".venv\Scripts\python.exe" manage.py runserver

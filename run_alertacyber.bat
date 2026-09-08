@echo off
setlocal
cd /d "%~dp0"
call venv\Scripts\activate.bat
python src\main.py >> data\run.log 2>&1
endlocal

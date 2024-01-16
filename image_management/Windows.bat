@echo off

:: Change cwd to the directory of the script
cd /d "%~dp0"

:: Check if Python is installed
python --version 2>nul
if errorlevel 1 (
    echo Error: Python is not installed. Please install Python.
    exit /b 1
)

:: Create a virtual environment named "image_handler"
python -m venv image_handler

:: Activate the virtual environment
call image_handler\Scripts\activate

:: Upgrade pip and ignore installation errors
pip install --upgrade pip || goto :continue

:continue
:: Install dependencies from "requirements.txt" ignoring errors
pip install -r requirements.txt || goto :execute_script

:execute_script
:: Execute the "main.py" script
python scripts/main.py

:: Deactivate the virtual environment
deactivate

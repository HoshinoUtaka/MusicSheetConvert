@echo off
REM One-shot setup: create a venv and install dependencies (Windows).
setlocal
set ROOT=%~dp0..
set PY=C:\Users\19473\.workbuddy\binaries\python\versions\3.13.12\python.exe
set VENV=C:\Users\19473\.workbuddy\binaries\python\envs\default

%PY% -m venv %VENV%
call %VENV%\Scripts\activate.bat
pip install --upgrade pip
pip install -r %ROOT%\requirements.txt
echo.
echo Install complete. Activate with: %VENV%\Scripts\activate
endlocal

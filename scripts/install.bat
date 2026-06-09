@echo off
REM One-shot setup: create a venv and install dependencies (Windows).
setlocal
set ROOT=%~dp0..
set PY=%path_to_your_python%
set VENV=%path_to_your_venv%

%PY% -m venv %VENV%
call %VENV%\Scripts\activate.bat
pip install --upgrade pip
pip install -r %ROOT%\requirements.txt
echo.
echo Install complete. Activate with: %VENV%\Scripts\activate
endlocal

@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo [error] Python not found on PATH. Install Python 3.11+ first: https://www.python.org/downloads/
  exit /b 1
)
python tools\one_click_install.py %*
exit /b %errorlevel%

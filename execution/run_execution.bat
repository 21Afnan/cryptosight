@echo off
title CryptoSight Execution Engine (Bybit Demo)
cd /d "%~dp0\..\.."
call venv\Scripts\activate.bat
python -m cryptosight.execution.main
pause
    
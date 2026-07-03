@echo off
cd /d "%NEUROG_PROJECT_ROOT%"
call "venv\Scripts\activate.bat"
python -m cryptosight.data.bybit.main
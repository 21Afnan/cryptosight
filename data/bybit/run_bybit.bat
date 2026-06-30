@echo off
cd /d "D:\Neurog_Internship"
call "venv\Scripts\activate.bat"
python -m cryptosight.data.bybit.main

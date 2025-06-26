@echo off
REM Deploy Tetris as a single EXE with all resources included
REM Make sure you have Python and PyInstaller installed
REM Usage: Double-click this file

set PYTHONPATH=src
pyinstaller --onefile --name Tetris src/main.py --add-data "src/tetris/resources;src/tetris/resources"

pause

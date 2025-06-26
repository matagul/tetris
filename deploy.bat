@echo off
REM Bu betik PyInstaller ile oyunu tek bir exe haline getirir.
REM PyInstaller yüklü olmalıdır.

pyinstaller --onefile --name Tetris src/main.py

pause

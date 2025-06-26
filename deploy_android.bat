@echo off
REM Deploy Tetris as a single APK for Android using Buildozer
REM Make sure you have Python, Kivy, and Buildozer installed (see https://kivy.org/doc/stable/guide/packaging-android.html)
REM Usage: Double-click this file

REM Copy all resources to the main directory for Buildozer
xcopy /E /I /Y src\tetris\resources resources

REM Create buildozer.spec if not exists
if not exist buildozer.spec (
    buildozer init
)

REM Edit buildozer.spec to include requirements
REM (You may need to do this manually for custom requirements)

REM Build the APK
buildozer -v android debug

REM APK will be in the bin/ folder
pause 
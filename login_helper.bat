@echo off
setlocal
cd /d "%~dp0"
title SpatialCraft - LLM Login Wizard
echo =================================================================
echo   SPATIALCRAFT // LOGIN WIZARD FOR CHATGPT & DEEPSEEK
echo =================================================================
echo.
echo Launching Google Chrome on your screen...
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe -u scripts\login_helper.py
) else (
    python -u scripts\login_helper.py
)
echo.
pause

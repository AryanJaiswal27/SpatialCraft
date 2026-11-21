@echo off
title SpatialCraft // Antigravity Guided Calibrator
cd /d "%~dp0"
echo =================================================================
echo   Launching Antigravity Guided Screen Calibrator...
echo   (No timer - take your time for each coordinate)
echo =================================================================
.\venv\Scripts\python.exe scripts\calibrate_clicks.py
pause

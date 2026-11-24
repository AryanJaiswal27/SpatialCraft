@echo off
title SpatialCraft // Physical Click Calibrator
cd /d "%~dp0"
echo =================================================================
echo   Launching SpatialCraft Multi-LLM Click Calibrator...
echo =================================================================
.\venv\Scripts\python.exe scripts\calibrate_clicks.py %*
pause

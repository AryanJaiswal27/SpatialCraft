@echo off
title SpatialCraft // Physical Click Desktop Daemon
cd /d "%~dp0"
echo =================================================================
echo   Launching SpatialCraft Physical Click Desktop Daemon...
echo =================================================================
.\venv\Scripts\python.exe scripts\physical_clicker.py --daemon
pause

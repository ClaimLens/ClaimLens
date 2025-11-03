@echo off
echo Starting ClaimLens Backend...
echo.
cd /d "%~dp0"
call conda activate claimlens
python app.py
pause

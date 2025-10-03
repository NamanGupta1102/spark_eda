@echo off
REM Setup Windows Task Scheduler for automated data updates
REM Run this as Administrator

echo Setting up automated data updates...

REM Create a scheduled task that runs every 3 hours
schtasks /create /tn "BostonDataUpdate" /tr "python \"%CD%\auto_data_updater.py\"" /sc hourly /mo 3 /ru "SYSTEM" /f

echo.
echo ✅ Scheduled task created: "BostonDataUpdate"
echo 📅 Runs every 3 hours
echo 🔧 To modify: Open Task Scheduler and find "BostonDataUpdate"
echo 🛑 To remove: schtasks /delete /tn "BostonDataUpdate" /f

pause


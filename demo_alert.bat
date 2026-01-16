@echo off
REM Demo script to trigger alerts and test Grafana/Slack integration

echo.
echo ====================================================================
echo Token Metrics Monitor - Demo Alert Generator
echo ====================================================================
echo.
echo This script will:
echo   1. Load environment variables from .env file
echo   2. Insert fake historical data (TVL drop scenario)
echo   3. Trigger anomaly detection
echo   4. Create alerts in the database
echo   5. Send test Slack notification (if configured)
echo.
echo You can then view the alerts in:
echo   - Grafana: http://localhost:3000
echo   - API: http://localhost:8000/alerts?status=open
echo   - Slack: Your configured channel
echo.
pause
echo.

REM Load environment variables from .env file
if exist .env (
    echo Loading environment variables from .env file...
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        REM Skip comments and empty lines
        echo %%a | findstr /r "^#" >nul
        if errorlevel 1 (
            if not "%%a"=="" (
                set "%%a=%%b"
            )
        )
    )
    echo Environment variables loaded successfully!
    echo.
) else (
    echo Warning: .env file not found in current directory.
    echo Slack notifications will not work without SLACK_WEBHOOK_URL.
    echo.
)

echo Running demo alert generator...
echo.

REM Run the demo script in the Podman container
podman run --rm --pod protocol-monitor-pod ^
  -e DB_HOST=localhost ^
  -e DB_PORT=5432 ^
  -e DB_NAME=protocol_monitor ^
  -e DB_USER=postgres ^
  -e DB_PASSWORD=postgres ^
  -e SLACK_WEBHOOK_URL=%SLACK_WEBHOOK_URL% ^
  protocol-monitor:latest python /app/demo_alert.py

echo.
echo ====================================================================
echo Demo complete!
echo ====================================================================
echo.
echo Open these URLs to see the results:
echo   - Grafana Dashboard: http://localhost:3000
echo   - API Alerts: http://localhost:8000/alerts?status=open
echo   - API Protocols: http://localhost:8000/protocols
echo.
pause

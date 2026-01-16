@echo off
REM Demo script to trigger alerts and test Grafana/Slack integration

echo.
echo ====================================================================
echo Token Metrics Monitor - Demo Alert Generator
echo ====================================================================
echo.
echo This script will:
echo   1. Insert fake historical data (TVL drop scenario)
echo   2. Trigger anomaly detection
echo   3. Create alerts in the database
echo   4. Send test Slack notification (if configured)
echo.
echo You can then view the alerts in:
echo   - Grafana: http://localhost:3000
echo   - API: http://localhost:8000/alerts?status=open
echo   - Slack: Your configured channel
echo.
pause
echo.

REM Run the demo script in the Podman container
podman run --rm --pod protocol-monitor-pod -e DB_HOST=localhost -e DB_PORT=5432 -e DB_NAME=protocol_monitor -e DB_USER=postgres -e DB_PASSWORD=postgres -e SLACK_WEBHOOK_URL=%SLACK_WEBHOOK_URL% protocol-monitor:latest python /app/demo_alert.py

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

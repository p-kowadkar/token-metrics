@echo off
REM Setup script for running Token Metrics Monitor with Podman (Windows)

echo.
echo ====================================================================
echo Setting up Token Metrics Monitor with Podman (Full Stack)...
echo ====================================================================
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
    echo Environment variables loaded!
    echo.
) else (
    echo Note: .env file not found. Using defaults.
    echo.
)

REM Create a pod (equivalent to docker-compose network)
echo [1/8] Creating pod...
podman pod create --name protocol-monitor-pod -p 8000:8000 -p 5432:5432 -p 3000:3000
if errorlevel 1 (
    echo ERROR: Failed to create pod
    pause
    exit /b 1
)

REM Start PostgreSQL container
echo [2/8] Starting PostgreSQL...
podman run -d --pod protocol-monitor-pod --name protocol-monitor-db -e POSTGRES_DB=protocol_monitor -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -v postgres_data:/var/lib/postgresql/data:Z docker.io/library/postgres:15-alpine
if errorlevel 1 (
    echo ERROR: Failed to start PostgreSQL
    pause
    exit /b 1
)

REM Wait for PostgreSQL to be ready
echo [3/8] Waiting for PostgreSQL to start...
timeout /t 5 /nobreak >nul

REM Initialize database schema
echo [4/8] Initializing database schema...
podman exec -i protocol-monitor-db psql -U postgres -d protocol_monitor < sql\schema.sql
if errorlevel 1 (
    echo ERROR: Failed to initialize database schema
    pause
    exit /b 1
)

REM Build the application image
echo [5/8] Building application image...
podman build -t protocol-monitor:latest .
if errorlevel 1 (
    echo ERROR: Failed to build application image
    pause
    exit /b 1
)

REM Run the monitoring pipeline once
echo [6/8] Running initial data ingestion...
podman run --rm --pod protocol-monitor-pod -e DB_HOST=localhost -e DB_PORT=5432 -e DB_NAME=protocol_monitor -e DB_USER=postgres -e DB_PASSWORD=postgres -e SLACK_WEBHOOK_URL=%SLACK_WEBHOOK_URL% protocol-monitor:latest python src/pipeline.py
if errorlevel 1 (
    echo WARNING: Data ingestion had issues, but continuing...
)

REM Start the API server
echo [7/8] Starting API server...
podman run -d --pod protocol-monitor-pod --name protocol-monitor-api -e DB_HOST=localhost -e DB_PORT=5432 -e DB_NAME=protocol_monitor -e DB_USER=postgres -e DB_PASSWORD=postgres protocol-monitor:latest python src/api.py
if errorlevel 1 (
    echo ERROR: Failed to start API server
    pause
    exit /b 1
)

REM Start Grafana
echo [8/8] Starting Grafana...
podman run -d --pod protocol-monitor-pod --name protocol-monitor-grafana -e GF_SECURITY_ADMIN_USER=admin -e GF_SECURITY_ADMIN_PASSWORD=admin -v grafana_data:/var/lib/grafana:Z -v %cd%\grafana\datasource.yml:/etc/grafana/provisioning/datasources/datasource.yml:Z -v %cd%\grafana\dashboards.yml:/etc/grafana/provisioning/dashboards/dashboards.yml:Z -v %cd%\grafana\dashboard.json:/etc/grafana/provisioning/dashboards/dashboard.json:Z docker.io/grafana/grafana:latest
if errorlevel 1 (
    echo ERROR: Failed to start Grafana
    pause
    exit /b 1
)

echo.
echo ====================================================================
echo Setup complete!
echo ====================================================================
echo.
echo Services are now running:
echo   * API: http://localhost:8000
echo   * Grafana: http://localhost:3000 (admin/admin)
echo.
echo Test the API:
echo   curl http://localhost:8000/protocols
echo   curl http://localhost:8000/alerts?status=open
echo.
echo To stop everything:
echo   podman pod stop protocol-monitor-pod
echo   podman pod rm protocol-monitor-pod
echo.
echo Or run: cleanup-podman.bat
echo ====================================================================
echo.
pause

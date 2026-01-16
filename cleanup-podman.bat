@echo off
REM Cleanup script for Token Metrics Monitor Podman pods (Windows)

echo.
echo ====================================================================
echo Cleaning up Token Metrics Monitor Podman pods...
echo ====================================================================
echo.

echo Stopping pod...
podman pod stop protocol-monitor-pod 2>nul

echo Removing pod and containers...
podman pod rm -f protocol-monitor-pod 2>nul

echo Removing volumes...
podman volume rm postgres_data 2>nul
podman volume rm grafana_data 2>nul

echo.
echo Verifying cleanup...
echo.
echo Pods:
podman pod ls

echo.
echo Containers:
podman ps -a

echo.
echo Volumes:
podman volume ls

echo.
echo ====================================================================
echo Cleanup complete!
echo ====================================================================
echo.
pause

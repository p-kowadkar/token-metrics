# Windows Setup Guide

This guide is for running the Token Metrics Monitor on Windows with Podman.

## Prerequisites

- **Podman Desktop** for Windows: https://podman-desktop.io/downloads
- **Python 3.11+**: https://www.python.org/downloads/
- **Git**: https://git-scm.com/download/win

## Quick Start

### Option 1: Using Batch Scripts (Easiest)

#### Clean Up Old Pods (if any)
```cmd
cleanup-podman.bat
```

#### Set Up and Run
```cmd
setup-podman.bat
```

This will:
- Create a Podman pod with all services
- Start PostgreSQL
- Initialize the database
- Build the application
- Run data ingestion
- Start the API server (port 8000)
- Start Grafana (port 3000)

#### Run Tests
```cmd
run_tests.bat
```

### Option 2: Manual Commands

If you prefer to run commands manually:

#### 1. Clean Up
```cmd
podman pod stop protocol-monitor-pod
podman pod rm -f protocol-monitor-pod
podman volume rm postgres_data grafana_data
```

#### 2. Create Pod
```cmd
podman pod create --name protocol-monitor-pod -p 8000:8000 -p 5432:5432 -p 3000:3000
```

#### 3. Start PostgreSQL
```cmd
podman run -d ^
  --pod protocol-monitor-pod ^
  --name protocol-monitor-db ^
  -e POSTGRES_DB=protocol_monitor ^
  -e POSTGRES_USER=postgres ^
  -e POSTGRES_PASSWORD=postgres ^
  -v postgres_data:/var/lib/postgresql/data:Z ^
  docker.io/library/postgres:15-alpine
```

#### 4. Wait and Initialize Database
```cmd
timeout /t 5 /nobreak
podman exec -i protocol-monitor-db psql -U postgres -d protocol_monitor < sql\schema.sql
```

#### 5. Build Application
```cmd
podman build -t protocol-monitor:latest .
```

#### 6. Start API
```cmd
podman run -d ^
  --pod protocol-monitor-pod ^
  --name protocol-monitor-api ^
  -e DB_HOST=localhost ^
  -e DB_PORT=5432 ^
  -e DB_NAME=protocol_monitor ^
  -e DB_USER=postgres ^
  -e DB_PASSWORD=postgres ^
  protocol-monitor:latest python src/api.py
```

#### 7. Start Grafana
```cmd
podman run -d ^
  --pod protocol-monitor-pod ^
  --name protocol-monitor-grafana ^
  -e GF_SECURITY_ADMIN_USER=admin ^
  -e GF_SECURITY_ADMIN_PASSWORD=admin ^
  -v grafana_data:/var/lib/grafana:Z ^
  -v %cd%\grafana\datasource.yml:/etc/grafana/provisioning/datasources/datasource.yml:Z ^
  -v %cd%\grafana\dashboards.yml:/etc/grafana/provisioning/dashboards/dashboards.yml:Z ^
  -v %cd%\grafana\dashboard.json:/etc/grafana/provisioning/dashboards/dashboard.json:Z ^
  docker.io/grafana/grafana:latest
```

## Access Services

- **API**: http://localhost:8000
- **Grafana**: http://localhost:3000 (Login: admin/admin)
- **PostgreSQL**: localhost:5432

## Testing the API

Open PowerShell or Command Prompt:

```cmd
curl http://localhost:8000/protocols
curl http://localhost:8000/alerts?status=open
```

Or open in browser:
- http://localhost:8000/protocols
- http://localhost:8000/alerts?status=open

## Slack Integration (Optional)

1. Get your Slack webhook URL from: https://api.slack.com/messaging/webhooks
2. Set environment variable before running setup:
   ```cmd
   set SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   setup-podman.bat
   ```

Or edit `.env` file and restart services.

## Troubleshooting

### Port Already in Use
If ports 8000, 5432, or 3000 are already in use:
```cmd
netstat -ano | findstr :8000
netstat -ano | findstr :5432
netstat -ano | findstr :3000
```

Kill the process or modify the pod creation command to use different ports.

### Podman Not Found
Make sure Podman Desktop is installed and the Podman CLI is in your PATH:
```cmd
podman --version
```

If not found, add Podman to your PATH or reinstall Podman Desktop.

### Permission Denied
Run Command Prompt or PowerShell as Administrator.

### Volume Mount Issues
On Windows, volume mounts with `:Z` flag may not work. Try removing `:Z`:
```cmd
-v postgres_data:/var/lib/postgresql/data
```

## Stopping Services

```cmd
podman pod stop protocol-monitor-pod
```

## Removing Everything

```cmd
cleanup-podman.bat
```

Or manually:
```cmd
podman pod rm -f protocol-monitor-pod
podman volume rm postgres_data grafana_data
```

## Alternative: Docker Desktop

If you prefer Docker over Podman, you can use Docker Desktop for Windows:

1. Install Docker Desktop: https://www.docker.com/products/docker-desktop/
2. Run:
   ```cmd
   docker-compose up --build
   ```

This is simpler but requires Docker Desktop (which may require a license for commercial use).

## Notes

- The `^` character is used for line continuation in Windows batch files
- Use backslashes `\` for paths in Windows
- Environment variables are set with `set VAR=value`
- The `timeout` command replaces `sleep` on Windows

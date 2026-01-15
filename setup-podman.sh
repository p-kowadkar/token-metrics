#!/bin/bash
# Setup script for running Token Metrics Monitor with Podman (Stretch Scope Edition)

set -e

echo "🚀 Setting up Token Metrics Monitor with Podman (Full Stack)..."

# Create a pod (equivalent to docker-compose network)
echo "📦 Creating pod..."
podman pod create --name protocol-monitor-pod -p 8000:8000 -p 5432:5432 -p 3000:3000

# Start PostgreSQL container
echo "🗄️  Starting PostgreSQL..."
podman run -d \
  --pod protocol-monitor-pod \
  --name protocol-monitor-db \
  -e POSTGRES_DB=protocol_monitor \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -v postgres_data:/var/lib/postgresql/data:Z \
  docker.io/library/postgres:15-alpine

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to start..."
sleep 5

# Initialize database schema
echo "📋 Initializing database schema..."
podman exec -i protocol-monitor-db psql -U postgres -d protocol_monitor < sql/schema.sql

# Build the application image
echo "🔨 Building application image..."
podman build -t protocol-monitor:latest .

# Run the monitoring pipeline once
echo "📊 Running initial data ingestion..."
podman run --rm \
  --pod protocol-monitor-pod \
  -e DB_HOST=localhost \
  -e DB_PORT=5432 \
  -e DB_NAME=protocol_monitor \
  -e DB_USER=postgres \
  -e DB_PASSWORD=postgres \
  -e SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}" \
  protocol-monitor:latest python src/pipeline.py

# Start the API server
echo "🌐 Starting API server..."
podman run -d \
  --pod protocol-monitor-pod \
  --name protocol-monitor-api \
  -e DB_HOST=localhost \
  -e DB_PORT=5432 \
  -e DB_NAME=protocol_monitor \
  -e DB_USER=postgres \
  -e DB_PASSWORD=postgres \
  protocol-monitor:latest python src/api.py

# Start Grafana
echo "📊 Starting Grafana..."
podman run -d \
  --pod protocol-monitor-pod \
  --name protocol-monitor-grafana \
  -e GF_SECURITY_ADMIN_USER=admin \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  -v grafana_data:/var/lib/grafana:Z \
  -v $(pwd)/grafana/datasource.yml:/etc/grafana/provisioning/datasources/datasource.yml:Z \
  -v $(pwd)/grafana/dashboards.yml:/etc/grafana/provisioning/dashboards/dashboards.yml:Z \
  -v $(pwd)/grafana/dashboard.json:/etc/grafana/provisioning/dashboards/dashboard.json:Z \
  docker.io/grafana/grafana:latest

echo ""
echo "✅ Setup complete!"
echo ""
echo "📡 Services are now running:"
echo "  • API: http://localhost:8000"
echo "  • Grafana: http://localhost:3000 (admin/admin)"
echo ""
echo "Test the API:"
echo "  curl http://localhost:8000/protocols"
echo "  curl http://localhost:8000/alerts?status=open"
echo ""
echo "To stop everything:"
echo "  podman pod stop protocol-monitor-pod"
echo "  podman pod rm protocol-monitor-pod"

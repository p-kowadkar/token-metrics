# Token Metrics - DeFi Protocol Monitoring Pipeline (Full Stack)

This project is a complete implementation of the Token Metrics take-home assignment, including all core requirements and stretch goals. It provides a production-ready monitoring pipeline for DeFi protocols.

## ⭐ Features

### Core Features

- **Data Ingestion**: Resiliently fetches TVL, APY, and utilization data from DefiLlama API.
- **PostgreSQL Database**: Stores historical data and alerts with an optimized schema.
- **Anomaly Detection**: Identifies critical events like TVL drops, low APY, and high utilization.
- **Health API**: A FastAPI application to expose protocol status, history, and alerts.
- **Resilience & Idempotency**: Built with request retries, timeout handling, and idempotent database writes.

### Stretch Scope Features

- **🚀 Docker & Docker Compose**: The entire stack (app, database, Grafana) can be launched with a single command: `docker-compose up`.
- **📊 Grafana Dashboard**: A pre-configured Grafana dashboard visualizes TVL, APY, and utilization over time, along with a table of recent alerts.
- **🔔 Slack Integration**: Sends real-time alert notifications to a configured Slack channel with detailed information.
- **🧪 Comprehensive Test Suite**: High test coverage for all components, including ingestion, anomaly detection, API, and notifications.

## 🚀 Getting Started

### Prerequisites

- Docker & Docker Compose (or Podman)
- A Slack Webhook URL (optional, for notifications)

### 1. Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
```

Edit the `.env` file to add your Slack Webhook URL (if you want to use Slack notifications):

```
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### 2. Run with Docker Compose (Recommended)

This is the easiest way to run the entire stack:

```bash
docker-compose up --build
```

This command will:
- Build the application Docker image.
- Start PostgreSQL, the API, the monitoring pipeline, and Grafana.
- The monitoring pipeline will run once on startup to populate data.

### 3. Run with Podman

If you use Podman, an automated script is provided:

```bash
chmod +x setup-podman.sh
./setup-podman.sh
```

### 4. Access Services

- **API**: [http://localhost:8000](http://localhost:8000)
- **Grafana**: [http://localhost:3000](http://localhost:3000) (Login: `admin` / `admin`)
- **PostgreSQL**: `localhost:5432`

## 🧪 Running Tests

A comprehensive test suite is included. To run the tests:

```bash
chmod +x run_tests.sh
./run_tests.sh
```

This will install test dependencies and run `pytest` with coverage reporting. The full report can be viewed at `htmlcov/index.html`.

## Project Structure

```
/Stretch_Scope
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
├── run_tests.sh
├── setup-podman.sh
├── grafana/
│   ├── dashboard.json
│   ├── dashboards.yml
│   └── datasource.yml
├── sql/
│   └── schema.sql
├── src/
│   ├── api.py
│   ├── anomaly_detector.py
│   ├── config.py
│   ├── database.py
│   ├── ingest.py
│   ├── notifications.py
│   └── pipeline.py
└── tests/
    ├── conftest.py
    ├── requirements-test.txt
    ├── test_api.py
    ├── test_anomaly_detector.py
    ├── test_ingest.py
    └── test_notifications.py
```

## API Endpoints

- `GET /protocols`: Get current status of all monitored protocols.
- `GET /protocols/{name}/history?days=30`: Get historical data for a protocol.
- `GET /alerts?status=open`: Get active alerts.
- `GET /health`: Health check for the API and database connection.

## High-Signal Checkpoints

- **Anomaly Thresholds**: The thresholds in `src/config.py` are set to reasonable defaults for major DeFi protocols but can be easily tuned.
- **Partial Failures**: The pipeline is designed to be resilient. A failure in fetching data for one protocol will not stop the others.
- **API Usefulness**: The API provides clean, essential data points (status, history, alerts) that are ideal for consumption by a mobile app frontend.

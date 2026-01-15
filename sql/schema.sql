-- Token Metrics Protocol Monitoring Schema

-- Table for storing protocol snapshots (TVL, APY, utilization)
CREATE TABLE IF NOT EXISTS protocol_snapshots (
    id SERIAL PRIMARY KEY,
    protocol_name VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    tvl_usd DECIMAL(20, 2),
    apy_7d DECIMAL(8, 4),
    utilization_rate DECIMAL(5, 4),  -- For lending protocols
    UNIQUE(protocol_name, timestamp)
);

-- Table for storing protocol alerts
CREATE TABLE IF NOT EXISTS protocol_alerts (
    id SERIAL PRIMARY KEY,
    protocol_name VARCHAR(50) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,  -- 'tvl_drop', 'apy_spike', 'utilization_high'
    severity VARCHAR(10) NOT NULL,     -- 'critical', 'warning', 'info'
    message TEXT NOT NULL,
    triggered_at TIMESTAMPTZ NOT NULL,
    resolved_at TIMESTAMPTZ
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_snapshots_protocol_time ON protocol_snapshots(protocol_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_protocol ON protocol_alerts(protocol_name);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON protocol_alerts(resolved_at) WHERE resolved_at IS NULL;

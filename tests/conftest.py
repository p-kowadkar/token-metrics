"""Pytest configuration and fixtures for testing."""

import pytest
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def sample_protocol_data():
    """Sample protocol snapshot data for testing."""
    return {
        'protocol_name': 'test-protocol',
        'timestamp': datetime.now(timezone.utc),
        'tvl_usd': Decimal('1000000.00'),
        'apy_7d': Decimal('5.25'),
        'utilization_rate': Decimal('0.7500')
    }


@pytest.fixture
def sample_alert_data():
    """Sample alert data for testing."""
    return {
        'protocol_name': 'test-protocol',
        'alert_type': 'tvl_drop',
        'severity': 'critical',
        'message': 'TVL dropped 25% in 24 hours',
        'triggered_at': datetime.now(timezone.utc)
    }


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing."""
    monkeypatch.setenv('DB_HOST', 'localhost')
    monkeypatch.setenv('DB_PORT', '5432')
    monkeypatch.setenv('DB_NAME', 'test_db')
    monkeypatch.setenv('DB_USER', 'test_user')
    monkeypatch.setenv('DB_PASSWORD', 'test_pass')
    monkeypatch.setenv('LOG_LEVEL', 'DEBUG')

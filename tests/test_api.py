"""Tests for the FastAPI endpoints."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from decimal import Decimal
from fastapi.testclient import TestClient

from api import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestAPIEndpoints:
    """Test cases for API endpoints."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "endpoints" in data
    
    @patch('api.db.get_cursor')
    @patch('api.PROTOCOLS', {'test-protocol': {}})
    def test_get_protocols(self, mock_cursor, client):
        """Test get protocols endpoint."""
        mock_cursor_obj = MagicMock()
        mock_cursor_obj.__enter__.return_value.fetchone.return_value = {
            'protocol_name': 'test-protocol',
            'tvl_usd': Decimal('1000000.00'),
            'apy_7d': Decimal('5.25'),
            'utilization_rate': Decimal('0.75'),
            'timestamp': datetime.now(timezone.utc)
        }
        mock_cursor.return_value = mock_cursor_obj
        
        with patch('api.determine_protocol_status', return_value='healthy'):
            response = client.get("/protocols")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]['name'] == 'test-protocol'
        assert data[0]['status'] == 'healthy'
    
    @patch('api.db.get_cursor')
    @patch('api.PROTOCOLS', {'test-protocol': {}})
    def test_get_protocol_history(self, mock_cursor, client):
        """Test get protocol history endpoint."""
        mock_cursor_obj = MagicMock()
        mock_cursor_obj.__enter__.return_value.fetchall.return_value = [
            {
                'timestamp': datetime.now(timezone.utc),
                'tvl_usd': Decimal('1000000.00'),
                'apy_7d': Decimal('5.25'),
                'utilization_rate': Decimal('0.75')
            }
        ]
        mock_cursor.return_value = mock_cursor_obj
        
        response = client.get("/protocols/test-protocol/history?days=30")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert 'timestamp' in data[0]
        assert 'tvl' in data[0]
    
    def test_get_protocol_history_not_found(self, client):
        """Test get protocol history for unknown protocol."""
        response = client.get("/protocols/unknown-protocol/history")
        assert response.status_code == 404
    
    @patch('api.db.get_cursor')
    def test_get_alerts_open(self, mock_cursor, client):
        """Test get open alerts endpoint."""
        mock_cursor_obj = MagicMock()
        mock_cursor_obj.__enter__.return_value.fetchall.return_value = [
            {
                'id': 1,
                'protocol_name': 'test-protocol',
                'alert_type': 'tvl_drop',
                'severity': 'critical',
                'message': 'Test alert',
                'triggered_at': datetime.now(timezone.utc),
                'resolved_at': None
            }
        ]
        mock_cursor.return_value = mock_cursor_obj
        
        response = client.get("/alerts?status=open")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]['status'] == 'open'
        assert data[0]['severity'] == 'critical'
    
    @patch('api.db.get_cursor')
    def test_get_alerts_all(self, mock_cursor, client):
        """Test get all alerts endpoint."""
        mock_cursor_obj = MagicMock()
        mock_cursor_obj.__enter__.return_value.fetchall.return_value = []
        mock_cursor.return_value = mock_cursor_obj
        
        response = client.get("/alerts?status=all")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @patch('api.db.get_cursor')
    def test_health_check_healthy(self, mock_cursor, client):
        """Test health check endpoint when healthy."""
        mock_cursor_obj = MagicMock()
        mock_cursor_obj.__enter__.return_value.execute.return_value = None
        mock_cursor.return_value = mock_cursor_obj
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
    
    @patch('api.db.get_cursor')
    def test_health_check_unhealthy(self, mock_cursor, client):
        """Test health check endpoint when unhealthy."""
        mock_cursor.side_effect = Exception("Database connection failed")
        
        response = client.get("/health")
        
        assert response.status_code == 503
        data = response.json()
        assert data['status'] == 'unhealthy'

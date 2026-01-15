"""Tests for the anomaly detection module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from anomaly_detector import AnomalyDetector


class TestAnomalyDetector:
    """Test cases for AnomalyDetector class."""
    
    def test_init(self):
        """Test detector initialization."""
        detector = AnomalyDetector()
        assert detector.thresholds is not None
        assert 'tvl_drop_24h_percent' in detector.thresholds
    
    @patch('anomaly_detector.db.get_cursor')
    def test_get_latest_snapshot(self, mock_cursor):
        """Test getting latest snapshot."""
        mock_cursor_obj = MagicMock()
        mock_cursor_obj.__enter__.return_value.fetchone.return_value = {
            'protocol_name': 'test-protocol',
            'tvl_usd': Decimal('1000000.00'),
            'apy_7d': Decimal('5.25'),
            'timestamp': datetime.now(timezone.utc)
        }
        mock_cursor.return_value = mock_cursor_obj
        
        detector = AnomalyDetector()
        snapshot = detector.get_latest_snapshot('test-protocol')
        
        assert snapshot is not None
        assert snapshot['protocol_name'] == 'test-protocol'
    
    @patch('anomaly_detector.db.get_cursor')
    def test_check_tvl_drop_critical(self, mock_cursor):
        """Test TVL drop detection for critical threshold."""
        now = datetime.now(timezone.utc)
        
        # Mock latest snapshot
        latest = {
            'protocol_name': 'test-protocol',
            'tvl_usd': Decimal('800000.00'),
            'timestamp': now
        }
        
        # Mock 24h ago snapshot
        snapshot_24h = {
            'protocol_name': 'test-protocol',
            'tvl_usd': Decimal('1000000.00'),
            'timestamp': now - timedelta(hours=24)
        }
        
        detector = AnomalyDetector()
        
        with patch.object(detector, 'get_latest_snapshot', return_value=latest):
            with patch.object(detector, 'get_snapshot_24h_ago', return_value=snapshot_24h):
                alert = detector.check_tvl_drop('test-protocol')
        
        assert alert is not None
        assert alert['alert_type'] == 'tvl_drop'
        assert alert['severity'] == 'critical'
        assert '20' in alert['message']
    
    @patch('anomaly_detector.db.get_cursor')
    def test_check_tvl_drop_no_alert(self, mock_cursor):
        """Test TVL drop detection when below threshold."""
        now = datetime.now(timezone.utc)
        
        latest = {
            'protocol_name': 'test-protocol',
            'tvl_usd': Decimal('950000.00'),
            'timestamp': now
        }
        
        snapshot_24h = {
            'protocol_name': 'test-protocol',
            'tvl_usd': Decimal('1000000.00'),
            'timestamp': now - timedelta(hours=24)
        }
        
        detector = AnomalyDetector()
        
        with patch.object(detector, 'get_latest_snapshot', return_value=latest):
            with patch.object(detector, 'get_snapshot_24h_ago', return_value=snapshot_24h):
                alert = detector.check_tvl_drop('test-protocol')
        
        assert alert is None
    
    @patch('anomaly_detector.db.get_cursor')
    def test_check_apy_low_warning(self, mock_cursor):
        """Test APY low detection."""
        latest = {
            'protocol_name': 'test-protocol',
            'apy_7d': Decimal('1.5'),
            'timestamp': datetime.now(timezone.utc)
        }
        
        detector = AnomalyDetector()
        
        with patch.object(detector, 'get_latest_snapshot', return_value=latest):
            alert = detector.check_apy_low('test-protocol')
        
        assert alert is not None
        assert alert['alert_type'] == 'apy_low'
        assert alert['severity'] == 'warning'
    
    @patch('anomaly_detector.db.get_cursor')
    def test_check_apy_low_no_alert(self, mock_cursor):
        """Test APY low detection when above threshold."""
        latest = {
            'protocol_name': 'test-protocol',
            'apy_7d': Decimal('5.5'),
            'timestamp': datetime.now(timezone.utc)
        }
        
        detector = AnomalyDetector()
        
        with patch.object(detector, 'get_latest_snapshot', return_value=latest):
            alert = detector.check_apy_low('test-protocol')
        
        assert alert is None
    
    @patch('anomaly_detector.db.get_cursor')
    @patch('anomaly_detector.PROTOCOLS', {'test-protocol': {'type': 'lending'}})
    def test_check_utilization_high_warning(self, mock_cursor):
        """Test high utilization detection."""
        latest = {
            'protocol_name': 'test-protocol',
            'utilization_rate': Decimal('0.97'),
            'timestamp': datetime.now(timezone.utc)
        }
        
        detector = AnomalyDetector()
        
        with patch.object(detector, 'get_latest_snapshot', return_value=latest):
            alert = detector.check_utilization_high('test-protocol')
        
        assert alert is not None
        assert alert['alert_type'] == 'utilization_high'
        assert alert['severity'] == 'warning'
    
    @patch('anomaly_detector.db.get_cursor')
    @patch('anomaly_detector.PROTOCOLS', {'test-protocol': {'type': 'lending'}})
    def test_check_utilization_high_no_alert(self, mock_cursor):
        """Test high utilization detection when below threshold."""
        latest = {
            'protocol_name': 'test-protocol',
            'utilization_rate': Decimal('0.85'),
            'timestamp': datetime.now(timezone.utc)
        }
        
        detector = AnomalyDetector()
        
        with patch.object(detector, 'get_latest_snapshot', return_value=latest):
            alert = detector.check_utilization_high('test-protocol')
        
        assert alert is None
    
    @patch('anomaly_detector.db.get_cursor')
    def test_save_alert_success(self, mock_cursor):
        """Test saving alert to database."""
        mock_cursor_obj = MagicMock()
        mock_cursor_obj.__enter__.return_value.fetchone.return_value = None
        mock_cursor.return_value = mock_cursor_obj
        
        detector = AnomalyDetector()
        alert_data = {
            'protocol_name': 'test-protocol',
            'alert_type': 'tvl_drop',
            'severity': 'critical',
            'message': 'Test alert',
            'triggered_at': datetime.now(timezone.utc)
        }
        
        result = detector.save_alert(alert_data)
        assert result is True
    
    @patch('anomaly_detector.db.get_cursor')
    def test_save_alert_duplicate(self, mock_cursor):
        """Test saving duplicate alert (should be skipped)."""
        mock_cursor_obj = MagicMock()
        mock_cursor_obj.__enter__.return_value.fetchone.return_value = {'id': 1}
        mock_cursor.return_value = mock_cursor_obj
        
        detector = AnomalyDetector()
        alert_data = {
            'protocol_name': 'test-protocol',
            'alert_type': 'tvl_drop',
            'severity': 'critical',
            'message': 'Test alert',
            'triggered_at': datetime.now(timezone.utc)
        }
        
        result = detector.save_alert(alert_data)
        assert result is False

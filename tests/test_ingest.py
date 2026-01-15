"""Tests for the data ingestion module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
import requests

from ingest import ProtocolDataFetcher


class TestProtocolDataFetcher:
    """Test cases for ProtocolDataFetcher class."""
    
    def test_init(self):
        """Test fetcher initialization."""
        fetcher = ProtocolDataFetcher()
        assert fetcher.session is not None
        assert 'User-Agent' in fetcher.session.headers
    
    @patch('ingest.requests.Session.get')
    def test_fetch_with_retry_success(self, mock_get):
        """Test successful data fetch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'tvl': 1000000}
        mock_get.return_value = mock_response
        
        fetcher = ProtocolDataFetcher()
        result = fetcher.fetch_with_retry('http://test.com/api')
        
        assert result == {'tvl': 1000000}
        assert mock_get.call_count == 1
    
    @patch('ingest.requests.Session.get')
    @patch('ingest.time.sleep')
    def test_fetch_with_retry_timeout(self, mock_sleep, mock_get):
        """Test fetch with timeout and retry."""
        mock_get.side_effect = requests.exceptions.Timeout()
        
        fetcher = ProtocolDataFetcher()
        result = fetcher.fetch_with_retry('http://test.com/api', max_retries=3)
        
        assert result is None
        assert mock_get.call_count == 3
        assert mock_sleep.call_count == 2
    
    @patch('ingest.requests.Session.get')
    @patch('ingest.time.sleep')
    def test_fetch_with_retry_5xx_error(self, mock_sleep, mock_get):
        """Test fetch with 5xx server error and retry."""
        mock_response = Mock()
        mock_response.status_code = 503
        mock_get.return_value = mock_response
        
        fetcher = ProtocolDataFetcher()
        result = fetcher.fetch_with_retry('http://test.com/api', max_retries=2)
        
        assert result is None
        assert mock_get.call_count == 2
    
    @patch('ingest.requests.Session.get')
    def test_fetch_with_retry_malformed_json(self, mock_get):
        """Test fetch with malformed JSON response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response
        
        fetcher = ProtocolDataFetcher()
        result = fetcher.fetch_with_retry('http://test.com/api')
        
        assert result is None
    
    def test_fetch_tvl_from_defillama_numeric(self):
        """Test TVL extraction from numeric response."""
        fetcher = ProtocolDataFetcher()
        
        with patch.object(fetcher, 'fetch_with_retry', return_value=1234567.89):
            tvl = fetcher.fetch_tvl_from_defillama('test-protocol')
            assert tvl == Decimal('1234567.89')
    
    def test_fetch_tvl_from_defillama_dict(self):
        """Test TVL extraction from dict response."""
        fetcher = ProtocolDataFetcher()
        
        with patch.object(fetcher, 'fetch_with_retry', return_value={'tvl': 9876543.21}):
            tvl = fetcher.fetch_tvl_from_defillama('test-protocol')
            assert tvl == Decimal('9876543.21')
    
    def test_fetch_tvl_from_defillama_none(self):
        """Test TVL extraction when fetch fails."""
        fetcher = ProtocolDataFetcher()
        
        with patch.object(fetcher, 'fetch_with_retry', return_value=None):
            tvl = fetcher.fetch_tvl_from_defillama('test-protocol')
            assert tvl is None
    
    def test_fetch_mock_apy(self):
        """Test mock APY fetching."""
        fetcher = ProtocolDataFetcher()
        
        apy = fetcher.fetch_mock_apy('aave-v3')
        assert apy == Decimal('3.45')
        
        apy = fetcher.fetch_mock_apy('compound-v3')
        assert apy == Decimal('4.25')
        
        apy = fetcher.fetch_mock_apy('unknown-protocol')
        assert apy is None
    
    def test_fetch_mock_utilization(self):
        """Test mock utilization fetching."""
        fetcher = ProtocolDataFetcher()
        
        util = fetcher.fetch_mock_utilization('aave-v3')
        assert util == Decimal('0.7250')
        
        util = fetcher.fetch_mock_utilization('unknown-protocol')
        assert util is None
    
    @patch.object(ProtocolDataFetcher, 'fetch_tvl_from_defillama')
    def test_fetch_protocol_data_success(self, mock_fetch_tvl):
        """Test successful protocol data fetching."""
        mock_fetch_tvl.return_value = Decimal('5000000.00')
        
        fetcher = ProtocolDataFetcher()
        data = fetcher.fetch_protocol_data('aave-v3')
        
        assert data is not None
        assert data['protocol_name'] == 'aave-v3'
        assert data['tvl_usd'] == Decimal('5000000.00')
        assert data['apy_7d'] == Decimal('3.45')
        assert data['utilization_rate'] == Decimal('0.7250')
    
    @patch.object(ProtocolDataFetcher, 'fetch_tvl_from_defillama')
    def test_fetch_protocol_data_failure(self, mock_fetch_tvl):
        """Test protocol data fetching when TVL fetch fails."""
        mock_fetch_tvl.return_value = None
        
        fetcher = ProtocolDataFetcher()
        data = fetcher.fetch_protocol_data('aave-v3')
        
        assert data is None
    
    def test_fetch_protocol_data_unknown_protocol(self):
        """Test fetching data for unknown protocol."""
        fetcher = ProtocolDataFetcher()
        data = fetcher.fetch_protocol_data('unknown-protocol')
        
        assert data is None

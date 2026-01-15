"""Data ingestion module for fetching protocol metrics."""

import requests
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Optional, List
from decimal import Decimal

from config import (
    PROTOCOLS, DEFILLAMA_API_BASE, REQUEST_TIMEOUT,
    MAX_RETRIES, RETRY_DELAY
)
from database import db

logger = logging.getLogger(__name__)


class ProtocolDataFetcher:
    """Fetches protocol data from various sources."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TokenMetrics-Monitor/1.0'
        })
    
    def fetch_with_retry(self, url: str, max_retries: int = MAX_RETRIES) -> Optional[Dict]:
        """Fetch data with retry logic for handling timeouts and errors."""
        for attempt in range(max_retries):
            try:
                logger.info(f"Fetching {url} (attempt {attempt + 1}/{max_retries})")
                response = self.session.get(url, timeout=REQUEST_TIMEOUT)
                
                # Handle 5xx errors
                if 500 <= response.status_code < 600:
                    logger.warning(f"Server error {response.status_code} for {url}")
                    if attempt < max_retries - 1:
                        time.sleep(RETRY_DELAY * (attempt + 1))
                        continue
                    return None
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout fetching {url}")
                if attempt < max_retries - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                    continue
                return None
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error fetching {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                    continue
                return None
                
            except ValueError as e:
                logger.error(f"Malformed response from {url}: {e}")
                return None
        
        return None
    
    def fetch_tvl_from_defillama(self, protocol_slug: str) -> Optional[Decimal]:
        """Fetch TVL data from DefiLlama API."""
        url = f"{DEFILLAMA_API_BASE}/tvl/{protocol_slug}"
        data = self.fetch_with_retry(url)
        
        if data and isinstance(data, (int, float)):
            return Decimal(str(data))
        elif data and isinstance(data, dict) and 'tvl' in data:
            return Decimal(str(data['tvl']))
        
        logger.warning(f"Could not extract TVL for {protocol_slug}")
        return None
    
    def fetch_protocol_data(self, protocol_key: str) -> Optional[Dict]:
        """Fetch comprehensive protocol data."""
        protocol_config = PROTOCOLS.get(protocol_key)
        if not protocol_config:
            logger.error(f"Unknown protocol: {protocol_key}")
            return None
        
        logger.info(f"Fetching data for {protocol_config['name']}")
        
        # Fetch TVL from DefiLlama
        tvl = self.fetch_tvl_from_defillama(protocol_config['defillama_slug'])
        
        # Mock APY and utilization data (in real implementation, fetch from on-chain)
        # For demonstration, we'll generate realistic mock data
        apy_7d = self.fetch_mock_apy(protocol_key)
        utilization_rate = None
        
        if protocol_config['type'] == 'lending':
            utilization_rate = self.fetch_mock_utilization(protocol_key)
        
        if tvl is None:
            logger.warning(f"Failed to fetch data for {protocol_key}")
            return None
        
        return {
            'protocol_name': protocol_key,
            'timestamp': datetime.now(timezone.utc),
            'tvl_usd': tvl,
            'apy_7d': apy_7d,
            'utilization_rate': utilization_rate
        }
    
    def fetch_mock_apy(self, protocol_key: str) -> Optional[Decimal]:
        """Mock APY fetching (replace with actual on-chain reads)."""
        # Simulate realistic APY values
        mock_apys = {
            'aave-v3': Decimal('3.45'),
            'compound-v3': Decimal('4.25')
        }
        return mock_apys.get(protocol_key)
    
    def fetch_mock_utilization(self, protocol_key: str) -> Optional[Decimal]:
        """Mock utilization rate fetching (replace with actual on-chain reads)."""
        # Simulate realistic utilization rates
        mock_utilization = {
            'aave-v3': Decimal('0.7250'),  # 72.5%
            'compound-v3': Decimal('0.6850')  # 68.5%
        }
        return mock_utilization.get(protocol_key)
    
    def save_snapshot(self, snapshot_data: Dict) -> bool:
        """Save protocol snapshot to database with idempotency."""
        try:
            with db.get_cursor(dict_cursor=False) as cursor:
                cursor.execute("""
                    INSERT INTO protocol_snapshots 
                    (protocol_name, timestamp, tvl_usd, apy_7d, utilization_rate)
                    VALUES (%(protocol_name)s, %(timestamp)s, %(tvl_usd)s, %(apy_7d)s, %(utilization_rate)s)
                    ON CONFLICT (protocol_name, timestamp) DO NOTHING
                """, snapshot_data)
                
                if cursor.rowcount > 0:
                    logger.info(f"Saved snapshot for {snapshot_data['protocol_name']}")
                    return True
                else:
                    logger.info(f"Snapshot already exists for {snapshot_data['protocol_name']} at {snapshot_data['timestamp']}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")
            return False
    
    def ingest_all_protocols(self) -> Dict[str, bool]:
        """Ingest data for all configured protocols."""
        results = {}
        
        for protocol_key in PROTOCOLS.keys():
            try:
                data = self.fetch_protocol_data(protocol_key)
                if data:
                    success = self.save_snapshot(data)
                    results[protocol_key] = success
                else:
                    results[protocol_key] = False
                    logger.error(f"Failed to fetch data for {protocol_key}")
            except Exception as e:
                logger.error(f"Error processing {protocol_key}: {e}", exc_info=True)
                results[protocol_key] = False
        
        return results


def run_ingestion():
    """Main ingestion function."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    fetcher = ProtocolDataFetcher()
    results = fetcher.ingest_all_protocols()
    
    success_count = sum(1 for v in results.values() if v)
    logger.info(f"Ingestion complete: {success_count}/{len(results)} protocols successful")
    
    return results


if __name__ == '__main__':
    run_ingestion()

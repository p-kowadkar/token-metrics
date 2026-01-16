"""Anomaly detection module for protocol monitoring."""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from decimal import Decimal

from database import db
from config import ANOMALY_THRESHOLDS, PROTOCOLS
from notifications import slack_notifier

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Detects anomalies in protocol metrics and triggers alerts."""
    
    def __init__(self):
        self.thresholds = ANOMALY_THRESHOLDS
    
    def get_latest_snapshot(self, protocol_name: str) -> Optional[Dict]:
        """Get the most recent snapshot for a protocol."""
        try:
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT protocol_name, timestamp, tvl_usd, apy_7d, utilization_rate
                    FROM protocol_snapshots
                    WHERE protocol_name = %s
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (protocol_name,))
                return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error fetching latest snapshot for {protocol_name}: {e}")
            return None
    
    def get_snapshot_24h_ago(self, protocol_name: str, current_time: datetime) -> Optional[Dict]:
        """Get snapshot from approximately 24 hours ago."""
        try:
            time_24h_ago = current_time - timedelta(hours=24)
            
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT protocol_name, timestamp, tvl_usd, apy_7d, utilization_rate
                    FROM protocol_snapshots
                    WHERE protocol_name = %s
                    AND timestamp <= %s
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (protocol_name, time_24h_ago))
                return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error fetching 24h snapshot for {protocol_name}: {e}")
            return None
    
    def check_tvl_drop(self, protocol_name: str) -> Optional[Dict]:
        """Check if TVL has dropped more than threshold in 24 hours."""
        latest = self.get_latest_snapshot(protocol_name)
        if not latest or not latest['tvl_usd']:
            return None
        
        snapshot_24h = self.get_snapshot_24h_ago(protocol_name, latest['timestamp'])
        if not snapshot_24h or not snapshot_24h['tvl_usd']:
            logger.info(f"No 24h historical data for {protocol_name}, skipping TVL drop check")
            return None
        
        current_tvl = float(latest['tvl_usd'])
        previous_tvl = float(snapshot_24h['tvl_usd'])
        
        if previous_tvl == 0:
            return None
        
        drop_percent = ((previous_tvl - current_tvl) / previous_tvl) * 100
        
        if drop_percent >= self.thresholds['tvl_drop_24h_percent']:
            return {
                'protocol_name': protocol_name,
                'alert_type': 'tvl_drop',
                'severity': 'critical',
                'message': f"TVL dropped {drop_percent:.2f}% in 24 hours (from ${previous_tvl:,.2f} to ${current_tvl:,.2f})",
                'triggered_at': datetime.now(timezone.utc)
            }
        
        return None
    
    def check_apy_low(self, protocol_name: str) -> Optional[Dict]:
        """Check if APY has dropped below threshold."""
        latest = self.get_latest_snapshot(protocol_name)
        if not latest or not latest['apy_7d']:
            return None
        
        current_apy = float(latest['apy_7d'])
        
        if current_apy < self.thresholds['apy_min_percent']:
            return {
                'protocol_name': protocol_name,
                'alert_type': 'apy_low',
                'severity': 'warning',
                'message': f"APY dropped below threshold: {current_apy:.2f}% (threshold: {self.thresholds['apy_min_percent']}%)",
                'triggered_at': datetime.now(timezone.utc)
            }
        
        return None
    
    def check_utilization_high(self, protocol_name: str) -> Optional[Dict]:
        """Check if utilization rate is too high for lending protocols."""
        protocol_config = PROTOCOLS.get(protocol_name)
        if not protocol_config or protocol_config['type'] != 'lending':
            return None
        
        latest = self.get_latest_snapshot(protocol_name)
        if not latest or not latest['utilization_rate']:
            return None
        
        current_utilization = float(latest['utilization_rate']) * 100  # Convert to percentage
        
        if current_utilization > self.thresholds['utilization_max_percent']:
            return {
                'protocol_name': protocol_name,
                'alert_type': 'utilization_high',
                'severity': 'warning',
                'message': f"Utilization rate critically high: {current_utilization:.2f}% (threshold: {self.thresholds['utilization_max_percent']}%)",
                'triggered_at': datetime.now(timezone.utc)
            }
        
        return None
    
    def save_alert(self, alert_data: Dict) -> bool:
        """Save alert to database, avoiding duplicates for recent alerts."""
        try:
            with db.get_cursor(dict_cursor=False) as cursor:
                # Check if similar alert exists in last hour (unresolved)
                cursor.execute("""
                    SELECT id FROM protocol_alerts
                    WHERE protocol_name = %s
                    AND alert_type = %s
                    AND resolved_at IS NULL
                    AND triggered_at > NOW() - INTERVAL '1 hour'
                    LIMIT 1
                """, (alert_data['protocol_name'], alert_data['alert_type']))
                
                if cursor.fetchone():
                    logger.info(f"Similar alert already exists for {alert_data['protocol_name']} - {alert_data['alert_type']}")
                    return False
                
                # Insert new alert
                cursor.execute("""
                    INSERT INTO protocol_alerts 
                    (protocol_name, alert_type, severity, message, triggered_at)
                    VALUES (%(protocol_name)s, %(alert_type)s, %(severity)s, %(message)s, %(triggered_at)s)
                """, alert_data)
                
                logger.warning(f"ALERT: {alert_data['severity'].upper()} - {alert_data['message']}")
                
                # Send Slack notification
                try:
                    slack_notifier.send_alert(alert_data)
                except Exception as e:
                    logger.error(f"Failed to send Slack notification: {e}")
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to save alert: {e}")
            return False
    
    def detect_anomalies(self, protocol_name: str) -> List[Dict]:
        """Run all anomaly checks for a protocol."""
        alerts = []
        
        # Check TVL drop
        tvl_alert = self.check_tvl_drop(protocol_name)
        if tvl_alert:
            alerts.append(tvl_alert)
            self.save_alert(tvl_alert)
        
        # Check APY low
        apy_alert = self.check_apy_low(protocol_name)
        if apy_alert:
            alerts.append(apy_alert)
            self.save_alert(apy_alert)
        
        # Check utilization high
        util_alert = self.check_utilization_high(protocol_name)
        if util_alert:
            alerts.append(util_alert)
            self.save_alert(util_alert)
        
        return alerts
    
    def detect_all_protocols(self) -> Dict[str, List[Dict]]:
        """Run anomaly detection for all protocols."""
        all_alerts = {}
        
        for protocol_name in PROTOCOLS.keys():
            try:
                alerts = self.detect_anomalies(protocol_name)
                all_alerts[protocol_name] = alerts
                
                if alerts:
                    logger.warning(f"Detected {len(alerts)} anomalies for {protocol_name}")
                else:
                    logger.info(f"No anomalies detected for {protocol_name}")
                    
            except Exception as e:
                logger.error(f"Error detecting anomalies for {protocol_name}: {e}", exc_info=True)
                all_alerts[protocol_name] = []
        
        return all_alerts


def run_anomaly_detection():
    """Main anomaly detection function."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    detector = AnomalyDetector()
    results = detector.detect_all_protocols()
    
    total_alerts = sum(len(alerts) for alerts in results.values())
    logger.info(f"Anomaly detection complete: {total_alerts} total alerts")
    
    return results


if __name__ == '__main__':
    run_anomaly_detection()

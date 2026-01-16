#!/usr/bin/env python3
"""
Demo script to trigger alerts for testing Grafana and Slack integration.
This script inserts fake historical data to trigger anomaly detection.
"""

import sys
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import db
from anomaly_detector import AnomalyDetector
from notifications import slack_notifier

def insert_fake_historical_data():
    """Insert fake historical data to trigger TVL drop alert."""
    print("📊 Inserting fake historical data to trigger alerts...")
    
    # Insert a snapshot from 24 hours ago with high TVL
    timestamp_24h_ago = datetime.now(timezone.utc) - timedelta(hours=24)
    
    with db.get_cursor() as cursor:
        # Insert high TVL snapshot from 24 hours ago
        cursor.execute("""
            INSERT INTO protocol_snapshots 
            (protocol_name, timestamp, tvl_usd, apy_7d, utilization_rate)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (protocol_name, timestamp) DO NOTHING
        """, (
            'aave-v3',
            timestamp_24h_ago,
            Decimal('50000000000.00'),  # $50 billion
            Decimal('5.00'),
            Decimal('0.75')
        ))
        
        # Insert current snapshot with much lower TVL (30% drop)
        cursor.execute("""
            INSERT INTO protocol_snapshots 
            (protocol_name, timestamp, tvl_usd, apy_7d, utilization_rate)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (protocol_name, timestamp) DO UPDATE
            SET tvl_usd = EXCLUDED.tvl_usd
        """, (
            'aave-v3',
            datetime.now(timezone.utc),
            Decimal('35000000000.00'),  # $35 billion (30% drop!)
            Decimal('1.50'),  # Low APY
            Decimal('0.97')   # High utilization
        ))
    
    print("✅ Fake data inserted successfully!")
    print(f"   - 24h ago: $50B TVL, 5% APY, 75% utilization")
    print(f"   - Now: $35B TVL (30% drop!), 1.5% APY (low!), 97% utilization (high!)")

def run_anomaly_detection():
    """Run anomaly detection to trigger alerts."""
    print("\n🔍 Running anomaly detection...")
    
    detector = AnomalyDetector()
    
    # Check for TVL drop
    print("   Checking TVL drop...")
    tvl_alert = detector.check_tvl_drop('aave-v3')
    if tvl_alert:
        print(f"   🚨 CRITICAL: {tvl_alert['message']}")
        detector.save_alert(tvl_alert)
    
    # Check for low APY
    print("   Checking low APY...")
    apy_alert = detector.check_apy_low('aave-v3')
    if apy_alert:
        print(f"   ⚠️  WARNING: {apy_alert['message']}")
        detector.save_alert(apy_alert)
    
    # Check for high utilization
    print("   Checking high utilization...")
    util_alert = detector.check_utilization_high('aave-v3')
    if util_alert:
        print(f"   ⚠️  WARNING: {util_alert['message']}")
        detector.save_alert(util_alert)
    
    print("✅ Anomaly detection complete!")

def test_slack_notification():
    """Test Slack notification."""
    print("\n🔔 Testing Slack notification...")
    
    if not slack_notifier.enabled:
        print("   ⚠️  Slack webhook not configured")
        print("   Set SLACK_WEBHOOK_URL environment variable to test Slack")
        return
    
    # Send test message
    success = slack_notifier.send_test_message()
    if success:
        print("   ✅ Test message sent to Slack!")
    else:
        print("   ❌ Failed to send test message")

def main():
    """Main demo function."""
    print("=" * 70)
    print("🎬 Token Metrics Monitor - Demo Alert Generator")
    print("=" * 70)
    print()
    
    try:
        # Step 1: Insert fake data
        insert_fake_historical_data()
        
        # Step 2: Run anomaly detection
        run_anomaly_detection()
        
        # Step 3: Test Slack
        test_slack_notification()
        
        print()
        print("=" * 70)
        print("✅ Demo complete!")
        print("=" * 70)
        print()
        print("📊 Next steps:")
        print("   1. Open Grafana: http://localhost:3000")
        print("   2. View the dashboard to see the data")
        print("   3. Check the alerts table for the triggered alerts")
        print("   4. Check your Slack channel for notifications (if configured)")
        print()
        print("🔍 Check alerts via API:")
        print("   curl http://localhost:8000/alerts?status=open")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

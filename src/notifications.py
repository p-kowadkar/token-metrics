"""Slack notification module for sending alerts."""

import os
import requests
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


# Sentinel value to distinguish between None and not-provided
_UNSET = object()

class SlackNotifier:
    """Send alerts to Slack channel via webhook."""
    
    def __init__(self, webhook_url: Optional[str] = _UNSET):
        # If webhook_url is explicitly provided (even if None), use it
        # Otherwise, fall back to environment variable
        if webhook_url is not _UNSET:
            self.webhook_url = webhook_url
        else:
            self.webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        self.enabled = bool(self.webhook_url)
        
        if not self.enabled:
            logger.info("Slack notifications disabled (no webhook URL configured)")
        else:
            logger.info("Slack notifications enabled")
    
    def _format_alert_message(self, alert: Dict) -> Dict:
        """Format alert data into Slack message blocks."""
        severity = alert['severity'].upper()
        protocol = alert['protocol_name']
        message = alert['message']
        
        # Choose color based on severity
        color_map = {
            'CRITICAL': '#FF0000',  # Red
            'WARNING': '#FFA500',   # Orange
            'INFO': '#0000FF'       # Blue
        }
        color = color_map.get(severity, '#808080')
        
        # Choose emoji based on severity
        emoji_map = {
            'CRITICAL': '🚨',
            'WARNING': '⚠️',
            'INFO': 'ℹ️'
        }
        emoji = emoji_map.get(severity, '📊')
        
        # Build Slack message
        slack_message = {
            "attachments": [
                {
                    "color": color,
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"{emoji} {severity} Alert: {protocol}",
                                "emoji": True
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Protocol:*\n{protocol}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Severity:*\n{severity}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Alert Type:*\n{alert['alert_type']}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Time:*\n{alert['triggered_at'].strftime('%Y-%m-%d %H:%M:%S UTC')}"
                                }
                            ]
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Details:*\n{message}"
                            }
                        }
                    ]
                }
            ]
        }
        
        return slack_message
    
    def send_alert(self, alert: Dict) -> bool:
        """
        Send an alert to Slack.
        
        Args:
            alert: Alert dictionary with keys: protocol_name, severity, alert_type, message, triggered_at
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Slack notifications disabled, skipping alert")
            return False
        
        try:
            message = self._format_alert_message(alert)
            
            response = requests.post(
                self.webhook_url,
                json=message,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Sent Slack notification for {alert['protocol_name']} - {alert['alert_type']}")
                return True
            else:
                logger.error(f"Failed to send Slack notification: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
            return False
    
    def send_test_message(self) -> bool:
        """Send a test message to verify Slack integration."""
        if not self.enabled:
            logger.warning("Cannot send test message: Slack webhook not configured")
            return False
        
        test_message = {
            "text": "✅ Token Metrics Monitor - Slack Integration Test",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Slack integration is working correctly! You will receive alerts here when anomalies are detected."
                    }
                }
            ]
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=test_message,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Test message sent successfully")
                return True
            else:
                logger.error(f"Failed to send test message: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending test message: {e}")
            return False


# Singleton instance
slack_notifier = SlackNotifier()


if __name__ == '__main__':
    """Test the Slack integration."""
    import sys
    from datetime import datetime, timezone
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if not os.getenv('SLACK_WEBHOOK_URL'):
        print("Error: SLACK_WEBHOOK_URL environment variable not set")
        print("Usage: SLACK_WEBHOOK_URL=https://hooks.slack.com/... python notifications.py")
        sys.exit(1)
    
    notifier = SlackNotifier()
    
    # Send test message
    print("Sending test message...")
    notifier.send_test_message()
    
    # Send sample alert
    print("Sending sample alert...")
    sample_alert = {
        'protocol_name': 'aave-v3',
        'severity': 'critical',
        'alert_type': 'tvl_drop',
        'message': 'TVL dropped 28.77% in 24 hours (from $50,000,000,000.00 to $35,612,811,836.00)',
        'triggered_at': datetime.now(timezone.utc)
    }
    notifier.send_alert(sample_alert)
    
    print("Done! Check your Slack channel.")

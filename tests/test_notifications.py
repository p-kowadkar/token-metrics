"""Tests for the Slack notifications module."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from notifications import SlackNotifier


class TestSlackNotifier:
    """Test cases for SlackNotifier class."""
    
    def test_init_without_webhook(self):
        """Test initialization without webhook URL."""
        notifier = SlackNotifier(webhook_url=None)
        assert notifier.enabled is False
    
    def test_init_with_webhook(self):
        """Test initialization with webhook URL."""
        notifier = SlackNotifier(webhook_url='https://hooks.slack.com/test')
        assert notifier.enabled is True
        assert notifier.webhook_url == 'https://hooks.slack.com/test'
    
    def test_format_alert_message_critical(self):
        """Test formatting critical alert message."""
        notifier = SlackNotifier(webhook_url='https://hooks.slack.com/test')
        
        alert = {
            'protocol_name': 'test-protocol',
            'severity': 'critical',
            'alert_type': 'tvl_drop',
            'message': 'TVL dropped 25%',
            'triggered_at': datetime.now(timezone.utc)
        }
        
        message = notifier._format_alert_message(alert)
        
        assert 'attachments' in message
        assert message['attachments'][0]['color'] == '#FF0000'
        assert 'blocks' in message['attachments'][0]
    
    def test_format_alert_message_warning(self):
        """Test formatting warning alert message."""
        notifier = SlackNotifier(webhook_url='https://hooks.slack.com/test')
        
        alert = {
            'protocol_name': 'test-protocol',
            'severity': 'warning',
            'alert_type': 'apy_low',
            'message': 'APY below threshold',
            'triggered_at': datetime.now(timezone.utc)
        }
        
        message = notifier._format_alert_message(alert)
        
        assert message['attachments'][0]['color'] == '#FFA500'
    
    @patch('notifications.requests.post')
    def test_send_alert_success(self, mock_post):
        """Test sending alert successfully."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        notifier = SlackNotifier(webhook_url='https://hooks.slack.com/test')
        
        alert = {
            'protocol_name': 'test-protocol',
            'severity': 'critical',
            'alert_type': 'tvl_drop',
            'message': 'Test alert',
            'triggered_at': datetime.now(timezone.utc)
        }
        
        result = notifier.send_alert(alert)
        
        assert result is True
        assert mock_post.call_count == 1
    
    @patch('notifications.requests.post')
    def test_send_alert_failure(self, mock_post):
        """Test sending alert with failure."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'Bad request'
        mock_post.return_value = mock_response
        
        notifier = SlackNotifier(webhook_url='https://hooks.slack.com/test')
        
        alert = {
            'protocol_name': 'test-protocol',
            'severity': 'critical',
            'alert_type': 'tvl_drop',
            'message': 'Test alert',
            'triggered_at': datetime.now(timezone.utc)
        }
        
        result = notifier.send_alert(alert)
        
        assert result is False
    
    def test_send_alert_disabled(self):
        """Test sending alert when notifications disabled."""
        notifier = SlackNotifier(webhook_url=None)
        
        alert = {
            'protocol_name': 'test-protocol',
            'severity': 'critical',
            'alert_type': 'tvl_drop',
            'message': 'Test alert',
            'triggered_at': datetime.now(timezone.utc)
        }
        
        result = notifier.send_alert(alert)
        
        assert result is False
    
    @patch('notifications.requests.post')
    def test_send_test_message_success(self, mock_post):
        """Test sending test message successfully."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        notifier = SlackNotifier(webhook_url='https://hooks.slack.com/test')
        result = notifier.send_test_message()
        
        assert result is True
        assert mock_post.call_count == 1
    
    def test_send_test_message_disabled(self):
        """Test sending test message when disabled."""
        notifier = SlackNotifier(webhook_url=None)
        result = notifier.send_test_message()
        
        assert result is False
    
    @patch('notifications.requests.post')
    def test_send_alert_exception(self, mock_post):
        """Test sending alert with exception."""
        mock_post.side_effect = Exception("Network error")
        
        notifier = SlackNotifier(webhook_url='https://hooks.slack.com/test')
        
        alert = {
            'protocol_name': 'test-protocol',
            'severity': 'critical',
            'alert_type': 'tvl_drop',
            'message': 'Test alert',
            'triggered_at': datetime.now(timezone.utc)
        }
        
        result = notifier.send_alert(alert)
        
        assert result is False

"""Configuration settings for the protocol monitor."""

import os
from typing import Dict, List

# Protocols to monitor
PROTOCOLS = {
    'aave-v3': {
        'name': 'Aave V3',
        'defillama_slug': 'aave-v3',
        'type': 'lending',
        'chain': 'ethereum'
    },
    'compound-v3': {
        'name': 'Compound V3',
        'defillama_slug': 'compound-v3',
        'type': 'lending',
        'chain': 'ethereum'
    }
}

# Anomaly detection thresholds
ANOMALY_THRESHOLDS = {
    'tvl_drop_24h_percent': 20.0,  # Critical if TVL drops >20% in 24h
    'apy_min_percent': 2.0,        # Warning if APY drops below 2%
    'utilization_max_percent': 95.0  # Warning if utilization >95%
}

# API settings
DEFILLAMA_API_BASE = 'https://api.llama.fi'
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Slack notifications (optional)
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL', None)

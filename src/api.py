"""FastAPI health endpoint for protocol monitoring."""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import logging

from database import db
from config import PROTOCOLS

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Protocol Monitor API",
    description="Health monitoring API for DeFi protocols",
    version="1.0.0"
)


def decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    return obj


def determine_protocol_status(protocol_name: str) -> str:
    """Determine protocol health status based on recent alerts."""
    try:
        with db.get_cursor() as cursor:
            # Check for critical alerts in last 24 hours
            cursor.execute("""
                SELECT severity FROM protocol_alerts
                WHERE protocol_name = %s
                AND resolved_at IS NULL
                AND triggered_at > NOW() - INTERVAL '24 hours'
                ORDER BY 
                    CASE severity
                        WHEN 'critical' THEN 1
                        WHEN 'warning' THEN 2
                        WHEN 'info' THEN 3
                    END
                LIMIT 1
            """, (protocol_name,))
            
            result = cursor.fetchone()
            if result:
                severity = result['severity']
                if severity == 'critical':
                    return 'critical'
                elif severity == 'warning':
                    return 'warning'
            
            return 'healthy'
            
    except Exception as e:
        logger.error(f"Error determining status for {protocol_name}: {e}")
        return 'unknown'


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Protocol Monitor API",
        "version": "1.0.0",
        "endpoints": [
            "/protocols",
            "/protocols/{name}/history",
            "/alerts"
        ]
    }


@app.get("/protocols")
async def get_protocols():
    """
    Get current status of all monitored protocols.
    
    Returns:
        List of protocols with name, tvl, apy, and health status
    """
    try:
        protocols_data = []
        
        for protocol_name in PROTOCOLS.keys():
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT protocol_name, tvl_usd, apy_7d, utilization_rate, timestamp
                    FROM protocol_snapshots
                    WHERE protocol_name = %s
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (protocol_name,))
                
                snapshot = cursor.fetchone()
                
                if snapshot:
                    status = determine_protocol_status(protocol_name)
                    
                    protocol_info = {
                        'name': protocol_name,
                        'tvl': decimal_to_float(snapshot['tvl_usd']) if snapshot['tvl_usd'] else None,
                        'apy': decimal_to_float(snapshot['apy_7d']) if snapshot['apy_7d'] else None,
                        'utilization': decimal_to_float(snapshot['utilization_rate']) if snapshot['utilization_rate'] else None,
                        'status': status,
                        'last_updated': snapshot['timestamp'].isoformat() if snapshot['timestamp'] else None
                    }
                    protocols_data.append(protocol_info)
                else:
                    protocols_data.append({
                        'name': protocol_name,
                        'tvl': None,
                        'apy': None,
                        'utilization': None,
                        'status': 'unknown',
                        'last_updated': None
                    })
        
        return JSONResponse(content=protocols_data)
        
    except Exception as e:
        logger.error(f"Error fetching protocols: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/protocols/{name}/history")
async def get_protocol_history(
    name: str,
    days: int = Query(default=30, ge=1, le=365, description="Number of days of history to retrieve")
):
    """
    Get historical data for a specific protocol.
    
    Args:
        name: Protocol name
        days: Number of days of history (default: 30)
    
    Returns:
        List of historical snapshots with timestamp, tvl, and apy
    """
    if name not in PROTOCOLS:
        raise HTTPException(status_code=404, detail=f"Protocol '{name}' not found")
    
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT timestamp, tvl_usd, apy_7d, utilization_rate
                FROM protocol_snapshots
                WHERE protocol_name = %s
                AND timestamp > NOW() - INTERVAL '%s days'
                ORDER BY timestamp DESC
            """, (name, days))
            
            history = cursor.fetchall()
            
            if not history:
                return JSONResponse(content=[])
            
            history_data = [
                {
                    'timestamp': record['timestamp'].isoformat() if record['timestamp'] else None,
                    'tvl': decimal_to_float(record['tvl_usd']) if record['tvl_usd'] else None,
                    'apy': decimal_to_float(record['apy_7d']) if record['apy_7d'] else None,
                    'utilization': decimal_to_float(record['utilization_rate']) if record['utilization_rate'] else None
                }
                for record in history
            ]
            
            return JSONResponse(content=history_data)
            
    except Exception as e:
        logger.error(f"Error fetching history for {name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/alerts")
async def get_alerts(
    status: str = Query(default="open", description="Filter by status: 'open', 'resolved', or 'all'")
):
    """
    Get alerts based on status filter.
    
    Args:
        status: Filter by 'open', 'resolved', or 'all' (default: 'open')
    
    Returns:
        List of active or resolved alerts
    """
    try:
        with db.get_cursor() as cursor:
            if status == "open":
                cursor.execute("""
                    SELECT id, protocol_name, alert_type, severity, message, triggered_at, resolved_at
                    FROM protocol_alerts
                    WHERE resolved_at IS NULL
                    ORDER BY triggered_at DESC
                """)
            elif status == "resolved":
                cursor.execute("""
                    SELECT id, protocol_name, alert_type, severity, message, triggered_at, resolved_at
                    FROM protocol_alerts
                    WHERE resolved_at IS NOT NULL
                    ORDER BY triggered_at DESC
                    LIMIT 100
                """)
            else:  # all
                cursor.execute("""
                    SELECT id, protocol_name, alert_type, severity, message, triggered_at, resolved_at
                    FROM protocol_alerts
                    ORDER BY triggered_at DESC
                    LIMIT 100
                """)
            
            alerts = cursor.fetchall()
            
            alerts_data = [
                {
                    'id': alert['id'],
                    'protocol_name': alert['protocol_name'],
                    'alert_type': alert['alert_type'],
                    'severity': alert['severity'],
                    'message': alert['message'],
                    'triggered_at': alert['triggered_at'].isoformat() if alert['triggered_at'] else None,
                    'resolved_at': alert['resolved_at'].isoformat() if alert['resolved_at'] else None,
                    'status': 'open' if alert['resolved_at'] is None else 'resolved'
                }
                for alert in alerts
            ]
            
            return JSONResponse(content=alerts_data)
            
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        with db.get_cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


if __name__ == "__main__":
    import uvicorn
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

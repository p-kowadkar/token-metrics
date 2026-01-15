"""Main pipeline orchestrator with resilience and idempotency."""

import logging
import sys
from datetime import datetime, timezone
from typing import Dict, List

from database import db
from ingest import ProtocolDataFetcher
from anomaly_detector import AnomalyDetector
from config import PROTOCOLS, LOG_LEVEL, LOG_FORMAT

logger = logging.getLogger(__name__)


class MonitoringPipeline:
    """Main monitoring pipeline with error handling and resilience."""
    
    def __init__(self):
        self.fetcher = ProtocolDataFetcher()
        self.detector = AnomalyDetector()
        self.run_id = datetime.now(timezone.utc).isoformat()
    
    def log_pipeline_run(self, status: str, details: Dict):
        """Log pipeline execution details."""
        logger.info(f"Pipeline run {self.run_id} - Status: {status}")
        logger.info(f"Details: {details}")
    
    def run_ingestion(self) -> Dict[str, bool]:
        """
        Run data ingestion with error handling.
        
        Returns:
            Dictionary mapping protocol names to success status
        """
        logger.info("Starting data ingestion phase...")
        results = {}
        
        for protocol_name in PROTOCOLS.keys():
            try:
                logger.info(f"Ingesting data for {protocol_name}")
                data = self.fetcher.fetch_protocol_data(protocol_name)
                
                if data:
                    success = self.fetcher.save_snapshot(data)
                    results[protocol_name] = success
                    
                    if success:
                        logger.info(f"✓ Successfully ingested {protocol_name}")
                    else:
                        logger.warning(f"⚠ Data already exists for {protocol_name} (idempotent)")
                else:
                    results[protocol_name] = False
                    logger.error(f"✗ Failed to fetch data for {protocol_name}")
                    
            except Exception as e:
                # Failed fetch doesn't crash the pipeline
                logger.error(f"✗ Error processing {protocol_name}: {e}", exc_info=True)
                results[protocol_name] = False
        
        success_count = sum(1 for v in results.values() if v)
        logger.info(f"Ingestion complete: {success_count}/{len(results)} protocols successful")
        
        return results
    
    def run_anomaly_detection(self) -> Dict[str, List[Dict]]:
        """
        Run anomaly detection with error handling.
        
        Returns:
            Dictionary mapping protocol names to detected alerts
        """
        logger.info("Starting anomaly detection phase...")
        all_alerts = {}
        
        for protocol_name in PROTOCOLS.keys():
            try:
                logger.info(f"Checking anomalies for {protocol_name}")
                alerts = self.detector.detect_anomalies(protocol_name)
                all_alerts[protocol_name] = alerts
                
                if alerts:
                    logger.warning(f"⚠ Detected {len(alerts)} anomalies for {protocol_name}")
                    for alert in alerts:
                        logger.warning(f"  - {alert['severity'].upper()}: {alert['message']}")
                else:
                    logger.info(f"✓ No anomalies detected for {protocol_name}")
                    
            except Exception as e:
                # Failed detection doesn't crash the pipeline
                logger.error(f"✗ Error detecting anomalies for {protocol_name}: {e}", exc_info=True)
                all_alerts[protocol_name] = []
        
        total_alerts = sum(len(alerts) for alerts in all_alerts.values())
        logger.info(f"Anomaly detection complete: {total_alerts} total alerts")
        
        return all_alerts
    
    def run(self) -> Dict:
        """
        Execute the complete monitoring pipeline.
        
        Returns:
            Summary of pipeline execution
        """
        start_time = datetime.now(timezone.utc)
        logger.info(f"=" * 60)
        logger.info(f"Starting monitoring pipeline run: {self.run_id}")
        logger.info(f"=" * 60)
        
        summary = {
            'run_id': self.run_id,
            'start_time': start_time.isoformat(),
            'ingestion_results': {},
            'anomaly_results': {},
            'status': 'success'
        }
        
        try:
            # Phase 1: Data Ingestion
            ingestion_results = self.run_ingestion()
            summary['ingestion_results'] = ingestion_results
            
            # Check if at least one protocol was successful
            if not any(ingestion_results.values()):
                logger.error("All protocols failed during ingestion")
                summary['status'] = 'partial_failure'
            
            # Phase 2: Anomaly Detection (runs even if some ingestions failed)
            anomaly_results = self.run_anomaly_detection()
            summary['anomaly_results'] = {
                protocol: len(alerts) 
                for protocol, alerts in anomaly_results.items()
            }
            
        except Exception as e:
            logger.error(f"Pipeline failed with critical error: {e}", exc_info=True)
            summary['status'] = 'failed'
            summary['error'] = str(e)
        
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        summary['end_time'] = end_time.isoformat()
        summary['duration_seconds'] = duration
        
        logger.info(f"=" * 60)
        logger.info(f"Pipeline run complete: {summary['status']}")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"=" * 60)
        
        self.log_pipeline_run(summary['status'], summary)
        
        return summary


def setup_logging():
    """Configure logging for the pipeline."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('pipeline.log')
        ]
    )


def main():
    """Main entry point for the monitoring pipeline."""
    setup_logging()
    
    try:
        # Initialize database schema
        logger.info("Initializing database schema...")
        db.init_schema()
        
        # Run pipeline
        pipeline = MonitoringPipeline()
        summary = pipeline.run()
        
        # Exit with appropriate code
        if summary['status'] == 'success':
            sys.exit(0)
        elif summary['status'] == 'partial_failure':
            sys.exit(1)
        else:
            sys.exit(2)
            
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(2)


if __name__ == '__main__':
    main()

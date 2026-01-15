"""Database connection and initialization module."""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager."""
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'protocol_monitor'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres')
        }
    
    @contextmanager
    def get_connection(self):
        """Get a database connection context manager."""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self, dict_cursor=True):
        """Get a database cursor context manager."""
        with self.get_connection() as conn:
            cursor_factory = RealDictCursor if dict_cursor else None
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
            finally:
                cursor.close()
    
    def init_schema(self, schema_file='sql/schema.sql'):
        """Initialize database schema from SQL file."""
        try:
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            
            with self.get_cursor(dict_cursor=False) as cursor:
                cursor.execute(schema_sql)
            
            logger.info("Database schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            raise


# Singleton instance
db = Database()

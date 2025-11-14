"""
Serverless-optimized database connection utilities for Vercel deployment.

This module provides connection pooling, health checks, and retry logic
specifically designed for serverless environments where connections
need to be managed efficiently due to function lifecycle constraints.
"""

import logging
import time
import threading
from typing import Dict, Any, Optional, Callable
from functools import wraps
from contextlib import contextmanager

from django.db import (
    connection, 
    connections,
    transaction, 
    DatabaseError as DjangoDatabaseError,
    OperationalError,
    InterfaceError,
)
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings

logger = logging.getLogger(__name__)


class ServerlessConnectionManager:
    """
    Connection manager optimized for serverless environments.
    
    Handles connection lifecycle, health checks, and cleanup
    specifically for Vercel's serverless function constraints.
    """
    
    def __init__(self):
        self._connection_cache = {}
        self._last_health_check = {}
        self._lock = threading.Lock()
        self.health_check_interval = 30  # seconds
        self.connection_timeout = 10  # seconds
        self.max_retries = 3
        self.retry_delay = 0.5  # seconds
    
    def get_connection(self, alias: str = 'default') -> Any:
        """
        Get a database connection with health checking and retry logic.
        
        Args:
            alias: Database alias name
            
        Returns:
            Database connection object
        """
        with self._lock:
            # Check if we need to perform health check
            if self._should_health_check(alias):
                self._perform_health_check(alias)
            
            return connections[alias]
    
    def _should_health_check(self, alias: str) -> bool:
        """Check if health check is needed for the connection."""
        last_check = self._last_health_check.get(alias, 0)
        return (time.time() - last_check) > self.health_check_interval
    
    def _perform_health_check(self, alias: str) -> bool:
        """
        Perform health check on database connection.
        
        Args:
            alias: Database alias name
            
        Returns:
            bool: True if connection is healthy
        """
        try:
            conn = connections[alias]
            
            # Close existing connection if it's stale
            if conn.connection is not None:
                try:
                    # Test the connection with a simple query
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT 1")
                        cursor.fetchone()
                except (OperationalError, InterfaceError):
                    # Connection is stale, close it
                    conn.close()
                    logger.info(f"Closed stale connection for {alias}")
            
            # Update last health check time
            self._last_health_check[alias] = time.time()
            
            logger.debug(f"Health check passed for connection {alias}")
            return True
            
        except Exception as e:
            logger.warning(f"Health check failed for connection {alias}: {e}")
            # Try to close the connection
            try:
                connections[alias].close()
            except Exception:
                pass
            return False
    
    def close_all_connections(self):
        """Close all database connections."""
        with self._lock:
            try:
                connections.close_all()
                self._connection_cache.clear()
                self._last_health_check.clear()
                logger.info("All database connections closed")
            except Exception as e:
                logger.error(f"Error closing connections: {e}")
    
    def get_connection_info(self, alias: str = 'default') -> Dict[str, Any]:
        """
        Get information about the database connection.
        
        Args:
            alias: Database alias name
            
        Returns:
            dict: Connection information
        """
        try:
            conn = connections[alias]
            db_settings = conn.settings_dict
            
            return {
                'alias': alias,
                'engine': db_settings.get('ENGINE', 'unknown'),
                'name': db_settings.get('NAME', 'unknown'),
                'host': db_settings.get('HOST', 'localhost'),
                'port': db_settings.get('PORT', 'default'),
                'conn_max_age': db_settings.get('CONN_MAX_AGE', 0),
                'is_connected': conn.connection is not None,
                'vendor': conn.vendor if hasattr(conn, 'vendor') else 'unknown',
                'last_health_check': self._last_health_check.get(alias, 0),
            }
        except Exception as e:
            return {
                'alias': alias,
                'error': str(e),
                'is_connected': False,
            }


# Global connection manager instance
connection_manager = ServerlessConnectionManager()


def with_db_retry(max_retries: int = 3, retry_delay: float = 0.5):
    """
    Decorator that adds retry logic for database operations.
    
    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                
                except (OperationalError, InterfaceError, DjangoDatabaseError) as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"Database operation failed (attempt {attempt + 1}/{max_retries + 1}): {e}"
                        )
                        
                        # Close connections to force reconnection
                        connection_manager.close_all_connections()
                        
                        # Wait before retry
                        if retry_delay > 0:
                            time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                    else:
                        logger.error(
                            f"Database operation failed after {max_retries + 1} attempts: {e}"
                        )
            
            # Re-raise the last exception if all retries failed
            raise last_exception
        
        return wrapper
    return decorator


@contextmanager
def serverless_transaction(alias: str = 'default', savepoint: bool = True):
    """
    Context manager for serverless-optimized database transactions.
    
    Args:
        alias: Database alias name
        savepoint: Whether to use savepoints for nested transactions
    """
    conn = connection_manager.get_connection(alias)
    
    if savepoint and conn.in_atomic_block:
        # Use savepoint for nested transactions
        sid = transaction.savepoint(using=alias)
        try:
            yield
            transaction.savepoint_commit(sid, using=alias)
        except Exception as e:
            transaction.savepoint_rollback(sid, using=alias)
            logger.error(f"Transaction savepoint rolled back: {e}")
            raise
    else:
        # Use atomic transaction
        try:
            with transaction.atomic(using=alias):
                yield
        except Exception as e:
            logger.error(f"Transaction rolled back: {e}")
            raise


class ServerlessHealthChecker:
    """
    Health checker optimized for serverless environments.
    """
    
    @staticmethod
    def check_database_health(alias: str = 'default') -> Dict[str, Any]:
        """
        Perform comprehensive database health check.
        
        Args:
            alias: Database alias name
            
        Returns:
            dict: Health check results
        """
        start_time = time.time()
        
        try:
            conn = connection_manager.get_connection(alias)
            
            # Test basic connectivity
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 as health_check")
                result = cursor.fetchone()
            
            # Test transaction capability
            with serverless_transaction(alias):
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1 as transaction_test")
                    cursor.fetchone()
            
            connection_time = (time.time() - start_time) * 1000
            
            return {
                'status': 'healthy',
                'connection_time_ms': round(connection_time, 2),
                'connection_info': connection_manager.get_connection_info(alias),
                'timestamp': time.time(),
                'checks_passed': ['connectivity', 'transactions'],
            }
        
        except Exception as e:
            connection_time = (time.time() - start_time) * 1000
            
            logger.error(f"Database health check failed for {alias}: {e}")
            
            return {
                'status': 'unhealthy',
                'error': str(e),
                'error_type': type(e).__name__,
                'connection_time_ms': round(connection_time, 2),
                'connection_info': connection_manager.get_connection_info(alias),
                'timestamp': time.time(),
            }
    
    @staticmethod
    def check_all_databases() -> Dict[str, Any]:
        """
        Check health of all configured databases.
        
        Returns:
            dict: Health check results for all databases
        """
        results = {}
        
        for alias in connections:
            results[alias] = ServerlessHealthChecker.check_database_health(alias)
        
        # Calculate overall health
        healthy_count = sum(1 for result in results.values() if result['status'] == 'healthy')
        total_count = len(results)
        
        return {
            'overall_status': 'healthy' if healthy_count == total_count else 'degraded',
            'healthy_databases': healthy_count,
            'total_databases': total_count,
            'databases': results,
            'timestamp': time.time(),
        }


def optimize_connection_settings():
    """
    Optimize database connection settings for serverless environment.
    
    This function should be called during Django startup to ensure
    optimal connection settings for Vercel deployment.
    """
    try:
        # Ensure connections are closed after each request
        for alias in connections:
            db_settings = connections[alias].settings_dict
            
            # Force connection close after each request
            if db_settings.get('CONN_MAX_AGE', 0) != 0:
                db_settings['CONN_MAX_AGE'] = 0
                logger.info(f"Set CONN_MAX_AGE=0 for database {alias}")
            
            # Enable connection health checks
            if not db_settings.get('CONN_HEALTH_CHECKS', False):
                db_settings['CONN_HEALTH_CHECKS'] = True
                logger.info(f"Enabled connection health checks for database {alias}")
            
            # Set connection timeout if not specified
            options = db_settings.setdefault('OPTIONS', {})
            if 'connect_timeout' not in options:
                options['connect_timeout'] = 10
                logger.info(f"Set connect_timeout=10 for database {alias}")
        
        logger.info("Database connection settings optimized for serverless")
        
    except Exception as e:
        logger.error(f"Failed to optimize connection settings: {e}")


def cleanup_connections():
    """
    Clean up database connections at the end of serverless function execution.
    
    This function should be called at the end of each serverless function
    to ensure proper cleanup and prevent connection leaks.
    """
    try:
        connection_manager.close_all_connections()
        logger.debug("Database connections cleaned up for serverless function end")
    except Exception as e:
        logger.error(f"Error during connection cleanup: {e}")


# Utility functions for common database operations with retry logic

@with_db_retry(max_retries=3)
def safe_execute_query(query: str, params: list = None, alias: str = 'default') -> list:
    """
    Execute a database query with retry logic.
    
    Args:
        query: SQL query string
        params: Query parameters
        alias: Database alias
        
    Returns:
        list: Query results
    """
    conn = connection_manager.get_connection(alias)
    
    with conn.cursor() as cursor:
        cursor.execute(query, params or [])
        return cursor.fetchall()


@with_db_retry(max_retries=3)
def safe_execute_transaction(operations: list, alias: str = 'default') -> bool:
    """
    Execute multiple database operations in a transaction with retry logic.
    
    Args:
        operations: List of (query, params) tuples
        alias: Database alias
        
    Returns:
        bool: True if successful
    """
    with serverless_transaction(alias):
        conn = connection_manager.get_connection(alias)
        
        with conn.cursor() as cursor:
            for query, params in operations:
                cursor.execute(query, params or [])
    
    return True
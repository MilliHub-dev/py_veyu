"""
Database utilities and error handling for the Veyu platform.

This module provides utilities for database error handling, connection management,
health checks, and transaction management with proper error recovery.
"""

import logging
import time
from typing import Dict, Any, Optional, Callable
from functools import wraps
from contextlib import contextmanager

from django.db import (
    connection, 
    transaction, 
    DatabaseError as DjangoDatabaseError,
    IntegrityError,
    OperationalError,
    DataError,
    InternalError,
    ProgrammingError,
    NotSupportedError
)
from django.db.models import Model
from django.core.exceptions import ValidationError
from django.conf import settings

from .exceptions import (
    DatabaseError, 
    DatabaseConstraintError, 
    ErrorCodes,
    VeyuException
)
from .logging_utils import get_logger

# Configure logger for database operations
logger = get_logger('veyu.database')


class DatabaseErrorHandler:
    """
    Utility class for handling database errors and converting them to VeyuExceptions.
    
    This class provides methods for converting Django database errors to
    structured VeyuException instances with appropriate error codes and messages.
    """
    
    @staticmethod
    def handle_database_error(error: Exception, operation: str = "database operation") -> VeyuException:
        """
        Convert Django database errors to VeyuExceptions
        
        Args:
            error: The original database error
            operation: Description of the operation that failed
            
        Returns:
            VeyuException: Structured exception with appropriate error code
        """
        error_message = str(error)
        
        # Handle specific database error types
        if isinstance(error, IntegrityError):
            # Extract constraint name if possible
            constraint_name = DatabaseErrorHandler._extract_constraint_name(error_message)
            
            if constraint_name:
                return DatabaseConstraintError(
                    constraint_name=constraint_name,
                    details={
                        'operation': operation,
                        'original_error': error_message,
                        'error_type': 'IntegrityError'
                    }
                )
            else:
                return DatabaseError(
                    message=f"Data integrity violation during {operation}",
                    error_code=ErrorCodes.DATABASE_CONSTRAINT_VIOLATION,
                    details={
                        'operation': operation,
                        'original_error': error_message,
                        'error_type': 'IntegrityError'
                    },
                    user_message="The operation conflicts with existing data."
                )
        
        elif isinstance(error, OperationalError):
            return DatabaseError(
                message=f"Database connection error during {operation}: {error_message}",
                error_code=ErrorCodes.DATABASE_CONNECTION_ERROR,
                details={
                    'operation': operation,
                    'original_error': error_message,
                    'error_type': 'OperationalError'
                },
                user_message="Database service is temporarily unavailable. Please try again later."
            )
        
        elif isinstance(error, DataError):
            return DatabaseError(
                message=f"Invalid data format during {operation}: {error_message}",
                error_code=ErrorCodes.VALIDATION_ERROR,
                details={
                    'operation': operation,
                    'original_error': error_message,
                    'error_type': 'DataError'
                },
                user_message="The provided data format is invalid."
            )
        
        elif isinstance(error, ProgrammingError):
            return DatabaseError(
                message=f"Database programming error during {operation}: {error_message}",
                error_code=ErrorCodes.API_INTERNAL_ERROR,
                details={
                    'operation': operation,
                    'original_error': error_message,
                    'error_type': 'ProgrammingError'
                },
                user_message="A database configuration error occurred. Please contact support."
            )
        
        elif isinstance(error, InternalError):
            return DatabaseError(
                message=f"Internal database error during {operation}: {error_message}",
                error_code=ErrorCodes.DATABASE_CONNECTION_ERROR,
                details={
                    'operation': operation,
                    'original_error': error_message,
                    'error_type': 'InternalError'
                },
                user_message="An internal database error occurred. Please try again later."
            )
        
        elif isinstance(error, NotSupportedError):
            return DatabaseError(
                message=f"Unsupported database operation during {operation}: {error_message}",
                error_code=ErrorCodes.API_INTERNAL_ERROR,
                details={
                    'operation': operation,
                    'original_error': error_message,
                    'error_type': 'NotSupportedError'
                },
                user_message="This operation is not supported. Please contact support."
            )
        
        else:
            # Generic database error
            return DatabaseError(
                message=f"Database error during {operation}: {error_message}",
                error_code=ErrorCodes.DATABASE_CONNECTION_ERROR,
                details={
                    'operation': operation,
                    'original_error': error_message,
                    'error_type': type(error).__name__
                },
                user_message="A database error occurred. Please try again later."
            )
    
    @staticmethod
    def _extract_constraint_name(error_message: str) -> Optional[str]:
        """
        Extract constraint name from database error message
        
        Args:
            error_message: Database error message
            
        Returns:
            str or None: Constraint name if found
        """
        # Common patterns for constraint names in error messages
        patterns = [
            'UNIQUE constraint failed: ',
            'duplicate key value violates unique constraint "',
            'violates foreign key constraint "',
            'violates check constraint "',
            'constraint "',
        ]
        
        for pattern in patterns:
            if pattern in error_message:
                start = error_message.find(pattern) + len(pattern)
                end = error_message.find('"', start)
                if end == -1:
                    end = error_message.find(' ', start)
                if end == -1:
                    end = len(error_message)
                
                constraint_name = error_message[start:end].strip('"')
                if constraint_name:
                    return constraint_name
        
        return None


def handle_database_errors(operation_name: str = None):
    """
    Decorator for handling database errors in functions and methods.
    
    This decorator catches database errors and converts them to VeyuExceptions
    with proper logging and error context.
    
    Args:
        operation_name: Optional name for the operation (defaults to function name)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__
            
            try:
                return func(*args, **kwargs)
            
            except DjangoDatabaseError as e:
                # Log the database error
                logger.error(
                    f"Database error in {op_name}",
                    context={
                        'function': func.__name__,
                        'operation': op_name,
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'args': str(args)[:200],  # Truncate for logging
                        'kwargs': str(kwargs)[:200],
                    }
                )
                
                # Convert to VeyuException
                raise DatabaseErrorHandler.handle_database_error(e, op_name)
            
            except ValidationError as e:
                # Handle Django validation errors
                logger.warning(
                    f"Validation error in {op_name}",
                    context={
                        'function': func.__name__,
                        'operation': op_name,
                        'validation_errors': str(e),
                    }
                )
                
                from .exceptions import ValidationError as VeyuValidationError
                raise VeyuValidationError(
                    message=f"Validation failed during {op_name}",
                    details={'django_validation_error': str(e)}
                )
        
        return wrapper
    return decorator


@contextmanager
def safe_transaction(savepoint_name: str = None):
    """
    Context manager for safe database transactions with automatic rollback.
    
    This context manager ensures that database transactions are properly
    handled with rollback on errors and proper logging.
    
    Args:
        savepoint_name: Optional savepoint name for nested transactions
    """
    if savepoint_name:
        # Use savepoint for nested transactions
        sid = transaction.savepoint()
        try:
            yield
            transaction.savepoint_commit(sid)
        except Exception as e:
            transaction.savepoint_rollback(sid)
            logger.error(
                f"Transaction rolled back to savepoint {savepoint_name}",
                context={
                    'savepoint_name': savepoint_name,
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                }
            )
            raise
    else:
        # Use full transaction
        try:
            with transaction.atomic():
                yield
        except Exception as e:
            logger.error(
                "Transaction rolled back",
                context={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                }
            )
            raise


class DatabaseHealthChecker:
    """
    Utility class for checking database health and connectivity.
    
    This class provides methods for testing database connections,
    checking query performance, and validating database configuration.
    """
    
    @staticmethod
    def check_connection() -> Dict[str, Any]:
        """
        Check database connection health
        
        Returns:
            dict: Health check results
        """
        start_time = time.time()
        
        try:
            # Test basic connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            connection_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return {
                'status': 'healthy',
                'connection_time_ms': round(connection_time, 2),
                'database_name': connection.settings_dict.get('NAME', 'unknown'),
                'database_engine': connection.settings_dict.get('ENGINE', 'unknown'),
                'timestamp': time.time(),
            }
        
        except Exception as e:
            connection_time = (time.time() - start_time) * 1000
            
            logger.error(
                "Database health check failed",
                context={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'connection_time_ms': round(connection_time, 2),
                }
            )
            
            return {
                'status': 'unhealthy',
                'error': str(e),
                'error_type': type(e).__name__,
                'connection_time_ms': round(connection_time, 2),
                'timestamp': time.time(),
            }
    
    @staticmethod
    def check_query_performance() -> Dict[str, Any]:
        """
        Check database query performance with sample queries
        
        Returns:
            dict: Performance check results
        """
        results = {}
        
        # Test queries for different models
        test_queries = [
            {
                'name': 'accounts_count',
                'query': "SELECT COUNT(*) FROM accounts_account",
                'description': 'Count of user accounts'
            },
            {
                'name': 'recent_accounts',
                'query': "SELECT id FROM accounts_account ORDER BY date_joined DESC LIMIT 10",
                'description': 'Recent user accounts'
            },
        ]
        
        for test in test_queries:
            start_time = time.time()
            
            try:
                with connection.cursor() as cursor:
                    cursor.execute(test['query'])
                    result = cursor.fetchall()
                
                query_time = (time.time() - start_time) * 1000
                
                results[test['name']] = {
                    'status': 'success',
                    'query_time_ms': round(query_time, 2),
                    'description': test['description'],
                    'result_count': len(result) if result else 0,
                }
            
            except Exception as e:
                query_time = (time.time() - start_time) * 1000
                
                results[test['name']] = {
                    'status': 'failed',
                    'error': str(e),
                    'query_time_ms': round(query_time, 2),
                    'description': test['description'],
                }
        
        return results
    
    @staticmethod
    def get_database_info() -> Dict[str, Any]:
        """
        Get database configuration and connection information
        
        Returns:
            dict: Database information
        """
        db_settings = connection.settings_dict
        
        return {
            'engine': db_settings.get('ENGINE', 'unknown'),
            'name': db_settings.get('NAME', 'unknown'),
            'host': db_settings.get('HOST', 'localhost'),
            'port': db_settings.get('PORT', 'default'),
            'user': db_settings.get('USER', 'unknown'),
            'conn_max_age': db_settings.get('CONN_MAX_AGE', 0),
            'autocommit': connection.get_autocommit(),
            'in_atomic_block': connection.in_atomic_block,
            'vendor': connection.vendor,
            'timezone': str(connection.timezone) if hasattr(connection, 'timezone') else 'unknown',
        }


def safe_bulk_create(
    model_class: Model,
    objects: list,
    batch_size: int = 1000,
    ignore_conflicts: bool = False
) -> Dict[str, Any]:
    """
    Safely perform bulk create operations with error handling
    
    Args:
        model_class: Django model class
        objects: List of model instances to create
        batch_size: Number of objects to create per batch
        ignore_conflicts: Whether to ignore conflicts (requires Django 2.2+)
        
    Returns:
        dict: Results of the bulk create operation
    """
    created_count = 0
    failed_count = 0
    errors = []
    
    # Process in batches
    for i in range(0, len(objects), batch_size):
        batch = objects[i:i + batch_size]
        
        try:
            with safe_transaction(f"bulk_create_batch_{i}"):
                created_objects = model_class.objects.bulk_create(
                    batch,
                    ignore_conflicts=ignore_conflicts
                )
                created_count += len(created_objects)
                
                logger.info(
                    f"Bulk created {len(created_objects)} {model_class.__name__} objects",
                    context={
                        'model': model_class.__name__,
                        'batch_size': len(batch),
                        'batch_start': i,
                        'created_count': len(created_objects),
                    }
                )
        
        except Exception as e:
            failed_count += len(batch)
            error_info = {
                'batch_start': i,
                'batch_size': len(batch),
                'error': str(e),
                'error_type': type(e).__name__,
            }
            errors.append(error_info)
            
            logger.error(
                f"Bulk create failed for {model_class.__name__} batch",
                context=error_info
            )
    
    return {
        'total_objects': len(objects),
        'created_count': created_count,
        'failed_count': failed_count,
        'success_rate': (created_count / len(objects)) * 100 if objects else 0,
        'errors': errors,
    }


def safe_bulk_update(
    objects: list,
    fields: list,
    batch_size: int = 1000
) -> Dict[str, Any]:
    """
    Safely perform bulk update operations with error handling
    
    Args:
        objects: List of model instances to update
        fields: List of field names to update
        batch_size: Number of objects to update per batch
        
    Returns:
        dict: Results of the bulk update operation
    """
    if not objects:
        return {'total_objects': 0, 'updated_count': 0, 'failed_count': 0, 'errors': []}
    
    model_class = type(objects[0])
    updated_count = 0
    failed_count = 0
    errors = []
    
    # Process in batches
    for i in range(0, len(objects), batch_size):
        batch = objects[i:i + batch_size]
        
        try:
            with safe_transaction(f"bulk_update_batch_{i}"):
                updated_objects = model_class.objects.bulk_update(batch, fields)
                updated_count += updated_objects
                
                logger.info(
                    f"Bulk updated {updated_objects} {model_class.__name__} objects",
                    context={
                        'model': model_class.__name__,
                        'batch_size': len(batch),
                        'batch_start': i,
                        'updated_count': updated_objects,
                        'fields': fields,
                    }
                )
        
        except Exception as e:
            failed_count += len(batch)
            error_info = {
                'batch_start': i,
                'batch_size': len(batch),
                'error': str(e),
                'error_type': type(e).__name__,
                'fields': fields,
            }
            errors.append(error_info)
            
            logger.error(
                f"Bulk update failed for {model_class.__name__} batch",
                context=error_info
            )
    
    return {
        'total_objects': len(objects),
        'updated_count': updated_count,
        'failed_count': failed_count,
        'success_rate': (updated_count / len(objects)) * 100 if objects else 0,
        'errors': errors,
    }
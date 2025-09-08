"""
Logging configuration for SolarMind application.

This module provides centralized logging setup with rotating file handlers
and structured log formatting.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from flask import Flask
from typing import Optional


def setup_logger(app: Flask, log_level: str = 'INFO') -> None:
    """
    Configure logging for the Flask application.
    
    Args:
        app: Flask application instance
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Create logs directory if it doesn't exist
    logs_dir = 'logs'
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Configure file handler
    log_file = os.path.join(logs_dir, 'solarmind.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    
    # Set formatter
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    file_handler.setFormatter(formatter)
    
    # Set log level
    level = getattr(logging, log_level.upper(), logging.INFO)
    file_handler.setLevel(level)
    
    # Add handler to app logger
    app.logger.addHandler(file_handler)
    app.logger.setLevel(level)
    
    # Initial log message
    app.logger.info('SolarMind application started')


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with standard configuration.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger


def log_error(logger: logging.Logger, error: Exception, context: Optional[str] = None) -> None:
    """
    Log an error with optional context information.
    
    Args:
        logger: Logger instance
        error: Exception to log
        context: Optional context description
    """
    error_msg = f"{type(error).__name__}: {str(error)}"
    if context:
        error_msg = f"{context} - {error_msg}"
    logger.error(error_msg, exc_info=True)
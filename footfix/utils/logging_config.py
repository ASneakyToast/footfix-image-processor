"""
Logging configuration for FootFix application.
Sets up appropriate logging handlers and formatters.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(log_level=logging.INFO, log_to_file=True):
    """
    Configure logging for the application.
    
    Args:
        log_level: Logging level (default: INFO)
        log_to_file: Whether to also log to a file (default: True)
    """
    # Create logs directory if it doesn't exist
    if log_to_file:
        log_dir = Path.home() / ".footfix" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file with timestamp
        log_file = log_dir / f"footfix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    # Console handler with simple format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with detailed format
    if log_to_file:
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Log everything to file
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
    
    # Set levels for specific loggers
    logging.getLogger('PIL').setLevel(logging.WARNING)  # Reduce PIL verbosity
    logging.getLogger('PySide6').setLevel(logging.WARNING)  # Reduce Qt verbosity
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info("FootFix application logging initialized")
    if log_to_file:
        logger.info(f"Log file: {log_file}")
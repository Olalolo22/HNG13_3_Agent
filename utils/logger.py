"""
Logging utility for Smart Read Later Organizer.
"""
import logging
import os
from pathlib import Path
from config.config import Config


def setup_logger(name: str) -> logging.Logger:
    """
    Set up logger with file and console handlers.
    
    Args:
        name: Logger name (usually __name__ from calling module)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path(Config.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler - for terminal output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    
    # File handler - for detailed logs
    file_handler = logging.FileHandler(Config.LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger
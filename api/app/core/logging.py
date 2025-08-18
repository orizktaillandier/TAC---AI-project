"""
Logging configuration for the API.
"""
import logging
import sys
from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel

from app.core.config import settings


class LogConfig(BaseModel):
    """Logging configuration."""
    
    LOGGER_NAME: str = "auto_classifier"
    LOG_FORMAT: str = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}"
    LOG_LEVEL: str = settings.LOG_LEVEL
    
    # Loguru handlers
    HANDLERS: List[Dict[str, Any]] = [
        {"sink": sys.stderr, "format": LOG_FORMAT, "level": LOG_LEVEL},
    ]


# Configure loguru logger
def setup_logging() -> None:
    """Set up logging with loguru."""
    config = LogConfig()
    
    # Remove default handlers
    logger.remove()
    
    # Add new handlers
    for handler in config.HANDLERS:
        logger.add(**handler)
    
    # Add file handler in production
    if settings.ENV == "production":
        logger.add(
            "logs/auto_classifier.log",
            rotation="10 MB",
            retention="7 days",
            format=config.LOG_FORMAT,
            level=config.LOG_LEVEL,
            compression="zip",
        )
    
    # Intercept standard logging
    class InterceptHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            # Get corresponding loguru level if it exists
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
            
            # Find caller from where the logged message was originated
            frame, depth = logging.currentframe(), 2
            while frame and frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1
            
            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )
    
    # Configure standard logging to use loguru
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Replace standard library loggers
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = [InterceptHandler()]


def get_logger() -> logger:
    """
    Get the configured logger.
    
    Returns:
        Loguru logger instance
    """
    return logger

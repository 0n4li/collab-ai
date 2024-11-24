from __future__ import annotations

import logging
import re
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Union, List

# Log Directory Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
APP_LOG_DIR = LOG_DIR / "app"
CONVERSATION_LOG_DIR = LOG_DIR / "conversations"

# Log Rotation Configuration
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5

# Logging Format Configuration
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Define valid log levels for type hints
LogLevel = Union[int, str]  # 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL' or their integer values

class LoggingError(Exception):
    """Custom exception for logging-related errors."""
    pass

def sanitize_filename(name: str) -> str:
    """
    Convert a string into a safe filename by removing or replacing unsafe characters.
    
    Args:
        name: The string to convert into a safe filename
        
    Returns:
        str: A string safe to use as a filename
    """
    return re.sub(r'[^\w\-]', '_', name)

def ensure_directory(path: Path) -> None:
    """
    Ensure a directory exists, creating it and its parents if necessary.
    
    Args:
        path: Path to the directory to ensure
        
    Raises:
        LoggingError: If directory creation fails
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise LoggingError(f"Failed to create directory {path}: {str(e)}")

def get_log_level(level: LogLevel) -> int:
    """
    Convert string log level to corresponding integer value.
    
    Args:
        level: Log level as string or int
        
    Returns:
        int: Numeric log level
    """
    if isinstance(level, str):
        return getattr(logging, level.upper())
    return level

def create_rotating_handler(
    log_file: Path,
    formatter: logging.Formatter,
    log_level: LogLevel
) -> logging.Handler:
    """
    Create a rotating file handler with the specified configuration.
    
    Args:
        log_file: Path to the log file
        formatter: Log formatter to use
        log_level: Logging level
        
    Returns:
        logging.Handler: Configured rotating file handler
    """
    handler = RotatingFileHandler(
        log_file,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT
    )
    handler.setFormatter(formatter)
    handler.setLevel(get_log_level(log_level))
    return handler

def setup_base_logger(
    name: str,
    log_level: LogLevel,
    handlers: List[logging.Handler],
    propagate: bool = False
) -> logging.Logger:
    """
    Set up a base logger with the specified configuration.
    
    Args:
        name: Logger name
        log_level: Logging level
        handlers: List of handlers to attach
        propagate: Whether to propagate messages to parent loggers
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(get_log_level(log_level))
    
    # Remove existing handlers if any
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add new handlers
    for handler in handlers:
        logger.addHandler(handler)
    
    logger.propagate = propagate
    return logger

class MarkdownFormatter(logging.Formatter):
    """Custom formatter for markdown-formatted log entries."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record in markdown format."""
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        message = record.getMessage()
        return f"[//]: # ({timestamp})\n{message}\n"

def setup_app_logger(
    name: str,
    log_level: LogLevel = 'INFO',
    print_debug: bool = False,
    custom_format: Optional[str] = None
) -> logging.Logger:
    """
    Set up application-level logger with rotation.
    
    Args:
        name: Name of the logger
        log_level: Logging level (default: 'INFO')
        print_debug: Whether to propagate messages to parent loggers
        custom_format: Custom logging format string
        
    Returns:
        logging.Logger: Configured logger instance
        
    Raises:
        LoggingError: If logger setup fails
    """
    try:
        ensure_directory(APP_LOG_DIR)
        
        # Create formatter
        formatter = logging.Formatter(custom_format or DEFAULT_LOG_FORMAT)
        
        # Create handlers
        handlers = [
            # logging.StreamHandler(),  # Console handler
            create_rotating_handler(  # File handler
                APP_LOG_DIR / f"{sanitize_filename(name)}.log",
                formatter,
                log_level
            )
        ]
        
        # Configure console handler
        handlers[0].setFormatter(formatter)
        handlers[0].setLevel(get_log_level(log_level))
        
        return setup_base_logger(name, log_level, handlers, print_debug)
    
    except Exception as e:
        raise LoggingError(f"Failed to setup app logger: {str(e)}")

def setup_conversation_logger(
    model1_name: str,
    model2_name: str,
    log_dir: Optional[Path] = None,
    log_filename: Optional[str] = None,
    log_level: LogLevel = 'INFO'
) -> logging.Logger:
    """
    Set up a new logger for a specific conversation with rotation.
    
    Args:
        model1_name: Name of the first model
        model2_name: Name of the second model
        log_dir: Custom directory for logs (default: CONVERSATION_LOG_DIR)
        log_filename: Custom filename for the log file
        log_level: Logging level (default: 'INFO')
        
    Returns:
        logging.Logger: Configured logger instance
        
    Raises:
        LoggingError: If logger setup fails
    """
    try:
        log_dir = log_dir or CONVERSATION_LOG_DIR
        if type(log_dir) == str:
            log_dir = Path(log_dir)
        ensure_directory(log_dir)
        
        # Generate logger name and file path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        logger_name = f"conversation_{timestamp}"
        
        if not log_filename:
            safe_model1_name = sanitize_filename(model1_name)
            safe_model2_name = sanitize_filename(model2_name)
            log_filename = f"{logger_name}_{safe_model1_name}_{safe_model2_name}.md"
        
        log_file = log_dir / log_filename
        
        # Clear the log_file and re-write
        with open(log_file, 'w') as f:
            f.write(f"_Conversation Log: {model1_name} and {model2_name}_\\\n")
            f.write(f"_Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n")
            f.write("\n---\n\n")
        
        # Create formatter and handler
        formatter = MarkdownFormatter()
        handler = create_rotating_handler(log_file, formatter, log_level)
        
        return setup_base_logger(logger_name, log_level, [handler], False)
    
    except Exception as e:
        raise LoggingError(f"Failed to setup conversation logger: {str(e)}")

def get_conversation_logs_path() -> Path:
    """Get the path to conversation logs directory."""
    return CONVERSATION_LOG_DIR

def get_app_logs_path() -> Path:
    """Get the path to application logs directory."""
    return APP_LOG_DIR

def setup_noop_logger() -> logging.Logger:
    """Set up a no-operation logger that doesn't output anything."""
    logger = logging.getLogger("noop")
    logger.addHandler(logging.NullHandler())
    return logger

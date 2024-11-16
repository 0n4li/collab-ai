import logging
import re
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pathlib import Path

# Get the project root directory (parent of src)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Define log directories
LOG_DIR = PROJECT_ROOT / "logs"
APP_LOG_DIR = LOG_DIR / "app"
CONVERSATION_LOG_DIR = LOG_DIR / "conversations"

# Constants for log rotation
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5

def sanitize_filename(name: str) -> str:
    """
    Convert a string into a safe filename by removing or replacing unsafe characters.
    
    Args:
        name: The string to convert into a safe filename
        
    Returns:
        A string safe to use as a filename
    """
    # Replace any non-alphanumeric characters (except hyphens and underscores) with underscores
    return re.sub(r'[^\w\-]', '_', name)

def ensure_log_directories():
    """Ensure all required log directories exist."""
    LOG_DIR.mkdir(exist_ok=True)
    APP_LOG_DIR.mkdir(exist_ok=True)
    CONVERSATION_LOG_DIR.mkdir(exist_ok=True)
    
def ensure_directory(path: Path):
    """Ensure a directory exists."""
    path.mkdir(parents=True, exist_ok=True)

def setup_app_logger(name: str) -> logging.Logger:
    """
    Set up application-level logger with rotation.
    
    Args:
        name: Name of the logger
        
    Returns:
        Configured logger instance
    """
    # Ensure directories exist
    ensure_log_directories()
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid adding handlers if they already exist
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # File handler with rotation
        log_file = APP_LOG_DIR / f"{sanitize_filename(name)}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT
        )
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger

class MarkdownFormatter(logging.Formatter):
    
    def format(self, record):
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        message = record.getMessage()
        formatted_message = f"[//]: # ({timestamp})\n{message}\n"    
        return formatted_message

def setup_conversation_logger(model1_name: str, model2_name: str, log_dir: Path = None, log_filename: str = None) -> logging.Logger:
    """
    Set up a new logger for a specific conversation with rotation, outputting in markdown format.
    
    Args:
        model1_name: Name of the first model
        model2_name: Name of the second model
        
    Returns:
        Configured logger instance
    """
    # Ensure directories exist
    ensure_log_directories()
    
    # Ensure Conversation Log Directory
    if not log_dir:
        log_dir = CONVERSATION_LOG_DIR
    ensure_directory(log_dir)
    
    # Sanitize model names for filename
    safe_model1_name = sanitize_filename(model1_name)
    safe_model2_name = sanitize_filename(model2_name)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger_name = f"conversation_{timestamp}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    # Create a new markdown file for this conversation
    if not log_filename:
        log_filename = f"{logger_name}_{safe_model1_name}_{safe_model2_name}.md"
    log_file = log_dir / log_filename
    
    # Write markdown header when creating the file
    if not log_file.exists():
        with open(log_file, 'w') as f:
            f.write(f"_Conversation Log: {model1_name} and {model2_name}_\\\n")
            f.write(f"_Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n")
            f.write("\n---\n\n")
    
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT
    )
    file_handler.setLevel(logging.INFO)
    
    formatter = MarkdownFormatter()
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    logger.propagate = False

    return logger

def get_conversation_logs_path() -> Path:
    """Get the path to conversation logs directory."""
    return CONVERSATION_LOG_DIR

def get_app_logs_path() -> Path:
    """Get the path to application logs directory."""
    return APP_LOG_DIR

def setup_noop_logger() -> logging.Logger:
    return logging.Logger("noop")

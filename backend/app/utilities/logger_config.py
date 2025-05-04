import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_file_logger(
    logger_name: str = __name__,
    log_dir: str = None,
    log_file: str = None,
    level=logging.INFO,
    max_bytes=5 * 1024 * 1024,  # 5 MB
    backup_count=5
):
    now = datetime.now()
    
    # Set default log directory and file name if not provided
    if log_dir is None:
        log_dir = f"logs/{now.strftime('%d-%m-%Y')}"
    if log_file is None:
        log_file = f"{now.strftime('%H-%M-%S-%f')}.log"

    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_file)

    # Create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.propagate = False  # Prevent logging from bubbling up

    # Formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler (Rotating)
    file_handler = RotatingFileHandler(
        log_path, maxBytes=max_bytes, backupCount=backup_count
    )
    file_handler.setFormatter(formatter)

    # Avoid duplicate handlers
    if not logger.handlers:
        logger.addHandler(file_handler)

    return logger

# Usage example
logger = setup_file_logger()
logger.info("Logger is set up and working!")
import logging
import os
from logging.handlers import RotatingFileHandler

def setup_file_logger(
    logger_name: str = __name__,
    log_dir: str = "logs",
    log_file: str = "app.log",
    level=logging.INFO,
    max_bytes=5 * 1024 * 1024,  # 5 MB
    backup_count=5
):
    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_file)

    # Create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.propagate = False  # Do not propagate to root logger (prevents console output)

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

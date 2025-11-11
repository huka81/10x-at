import logging
import sys
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
import os

import os
from dotenv import load_dotenv

load_dotenv()

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
if BASE_PATH.endswith("python"):
    BASE_PATH = BASE_PATH[: -len("python")]

ENV_NAME = os.getenv("ENV_NAME")
LOGS_PATH = os.getenv("LOGS_PATH").replace("{BASE_PATH}", BASE_PATH)
C_LOG_BASE_NAME = "10xdev-at"
C_LOG_FORMAT = "[%(asctime)-15s][%(funcName)s:%(lineno)d] %(message)s"

# Ensure the log directory exists
LOGS_PATH = Path(LOGS_PATH)
LOGS_PATH.mkdir(parents=True, exist_ok=True)

# Configure root logger only once
root_logger = logging.getLogger()
if not root_logger.handlers:
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(C_LOG_FORMAT))

    # File handler with rotation
    log_filename = LOGS_PATH / f"{C_LOG_BASE_NAME}.log"
    file_handler = TimedRotatingFileHandler(
        log_filename,
        when="midnight",  # Rotate at midnight
        backupCount=30,  # Keep logs for the last 30 days
    )
    file_handler.setFormatter(logging.Formatter(C_LOG_FORMAT))

    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.setLevel(logging.INFO)


def get_logger(name):
    """
    Get a logger with the specified name.
    This ensures we don't add duplicate handlers when importing modules.

    Args:
        name: The name of the logger, typically __name__

    Returns:
        A configured logger instance
    """
    logger = logging.getLogger(name)
    # Don't propagate to root logger to avoid duplicate messages
    logger.propagate = True
    return logger

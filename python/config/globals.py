"""Global configuration constants."""

from pathlib import Path

# Logging configuration
LOGS_PATH = Path("logs")
C_LOG_BASE_NAME = "app"
C_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

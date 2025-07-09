"""
Debug adapter logging configuration
Logs go to both stderr and debug_adapter.log file
"""

import logging
import sys
from pathlib import Path


def setup_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    """
    Setup logger with output to stderr and file.

    Args:
        name: Logger name
        level: Logging level

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler (stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    try:
        # Log file path in project root (ink-sandbox-trace/)
        # utils/logger.py -> src -> ink-dap-server -> ink-sandbox-trace
        log_file = Path(__file__).parent.parent.parent / "debug_adapter.log"

        # Create file handler (overwrites file on each startup)
        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Log successful file creation
        logger.info(f"Logs are also saved to file: {log_file}")

    except Exception as e:
        # If file creation fails - continue with console logging only
        logger.warning(f"Could not create log file: {e}")

    return logger
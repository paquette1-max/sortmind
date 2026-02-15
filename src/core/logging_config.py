"""Logging configuration for AI File Organizer."""
import logging
from pathlib import Path


def setup_logging(config):
    """Setup application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

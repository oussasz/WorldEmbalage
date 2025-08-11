# Logging configuration using loguru
from __future__ import annotations
import sys
from loguru import logger
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[2] / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / 'app.log'

# Remove default handler to avoid duplicate logs
logger.remove()

# Console handler
logger.add(sys.stderr, level='DEBUG', enqueue=True, colorize=True,
           format='<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>')

# File handler with rotation
logger.add(LOG_FILE, level='INFO', rotation='10 MB', retention='30 days', enqueue=True,
           format='{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}')

__all__ = ['logger']

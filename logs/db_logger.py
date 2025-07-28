import logging
from logging.handlers import RotatingFileHandler
import os

os.makedirs("logs", exist_ok=True)

logger = logging.getLogger("database_logger")
logger.setLevel(logging.DEBUG)

rotating_handler = RotatingFileHandler("logs/database.log", maxBytes=5*1024*1024, backupCount=3)
stream_handler = logging.StreamHandler()

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
rotating_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

if not logger.hasHandlers():
    logger.addHandler(rotating_handler)
    logger.addHandler(stream_handler)

import logging.handlers
from logging import Logger
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR /'logger'

core_logger: Logger = logging.getLogger("Servise_bot")
core_logger.setLevel(level=logging.INFO)
file = logging.handlers.RotatingFileHandler(DB_PATH/"logs_core.log", encoding="utf-8", maxBytes=100_000, backupCount=10)
formatter = logging.Formatter( "%(asctime)s | %(levelname)s | %(message)s")
file.setFormatter(formatter)
if not core_logger.handlers:
    core_logger.addHandler(file)

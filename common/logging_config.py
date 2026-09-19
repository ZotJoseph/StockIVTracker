from pathlib import Path

import logging
from logging.handlers import RotatingFileHandler

def setup_logging():

    #
    log_dir = Path("logs")

    log_dir.mkdir(exist_ok = True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler = RotatingFileHandler(
        log_dir/"app.log",
        maxBytes=10_000_000,  # 10 MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)

    #use logging instead of print and it should show up in terminal
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler]
    )
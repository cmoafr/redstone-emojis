from datetime import datetime
import logging
import os
from typing import Literal

def get_log_filename() -> str:
    """
    Returns the log filename.
    """

    os.makedirs("logs", exist_ok=True)

    base = f"logs/{ datetime.now().strftime('%Y-%m-%d') }_{{}}.log" # Format "YYYY-MM-DD_N.log"
    i = 0
    while os.path.exists(base.format(i)):
        i += 1
    return base.format(i)

def get_logger(name: str) -> logging.Logger:
    """
    Returns the logger for the given name.
    """

    class LevelFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> Literal[True]:
            if record.levelno == logging.WARNING:
                record.levelname = "WARN "
            elif record.levelno == logging.CRITICAL:
                record.levelname = "CRIT!"
            else:
                record.levelname = (record.levelname + " ")[:5]
            return True

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addFilter(LevelFilter())
    formatter = logging.Formatter("%(asctime)s [%(levelname)s]: %(message)s", datefmt="%H:%M:%S")

    # To write to a file
    file_handler = logging.FileHandler(get_log_filename())
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # To write to the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

import logging
import os
from logging.config import dictConfig


LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = os.getenv("LOG_DIR", "logs")


def setup_logging() -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, "app.log")

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "level": LOG_LEVEL,
                },
                "file": {
                    "class": "logging.FileHandler",
                    "filename": log_path,
                    "formatter": "default",
                    "level": LOG_LEVEL,
                },
            },
            "root": {
                "level": LOG_LEVEL,
                "handlers": ["console", "file"],
            },
        }
    )


def get_logger(name: str | None = None) -> logging.Logger:
    return logging.getLogger(name or "ai_job_assistant")

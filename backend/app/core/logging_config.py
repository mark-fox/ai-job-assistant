import logging
import os
from logging.config import dictConfig

from app.core.config import settings


def setup_logging() -> None:
    os.makedirs(settings.log_dir, exist_ok=True)
    log_path = os.path.join(settings.log_dir, "app.log")

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
                    "level": settings.log_level,
                },
                "file": {
                    "class": "logging.FileHandler",
                    "filename": log_path,
                    "formatter": "default",
                    "level": settings.log_level,
                },
            },
            "root": {
                "level": settings.log_level,
                "handlers": ["console", "file"],
            },
        }
    )


def get_logger(name: str | None = None) -> logging.Logger:
    return logging.getLogger(name or "ai_job_assistant")

from dataclasses import dataclass
import os


@dataclass
class Settings:
    app_env: str
    database_url: str
    log_level: str
    log_dir: str


def load_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./ai_job_assistant.db"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_dir=os.getenv("LOG_DIR", "logs"),
    )


settings = load_settings()

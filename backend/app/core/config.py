from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    app_env: str
    database_url: str
    log_level: str
    log_dir: str
    llm_provider: str
    openai_api_key: str | None
    openai_model: str


def load_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./ai_job_assistant.db"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_dir=os.getenv("LOG_DIR", "logs"),
        llm_provider=os.getenv("LLM_PROVIDER", "stub"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    )


settings = load_settings()

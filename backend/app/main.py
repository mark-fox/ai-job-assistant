import time

from fastapi import FastAPI
from sqlalchemy import text
from starlette.requests import Request
from starlette.middleware.cors import CORSMiddleware

from app.api.users import router as users_router
from app.api.resume import router as resume_router
from app.api.answers import router as answers_router
from app.core.db import Base, engine
from app.core.logging_config import get_logger, setup_logging
from app.core.config import settings

setup_logging()
logger = get_logger("ai_job_assistant.api")

app = FastAPI(
    title="AI Job Assistant Backend",
    version="0.1.0",
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(users_router)
app.include_router(resume_router)
app.include_router(answers_router)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000

    logger.info(
        "request completed method=%s path=%s status=%d duration_ms=%.2f",
        request.method,
        request.url.path,
                response.status_code,
        duration_ms,
    )
    return response


@app.get("/status")
def get_status():
    db_ok = False

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        db_ok = True
    except Exception as exc:
        logger.error("database health check failed: %s", exc)

    overall_status = "ok" if db_ok else "degraded"

    return {
        "status": overall_status,
        "version": app.version,
        "environment": settings.app_env,
        "llm_provider": settings.llm_provider,
        "checks": {
            "database": "ok" if db_ok else "error",
        },
    }

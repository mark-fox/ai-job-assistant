from fastapi import FastAPI

from app.api.users import router as users_router
from app.api.resume import router as resume_router
from app.api.answers import router as answers_router
from app.core.db import Base, engine

app = FastAPI(
    title="AI Job Assistant Backend",
    version="0.1.0",
)

Base.metadata.create_all(bind=engine)

app.include_router(users_router)
app.include_router(resume_router)
app.include_router(answers_router)


@app.get("/status")
def get_status():
    return {"status": "ok"}

from fastapi import FastAPI

app = FastAPI(
    title="AI Job Assistant Backend",
    version="0.1.0",
)


@app.get("/status")
def get_status():
    return {"status": "ok"}

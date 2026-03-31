from fastapi import FastAPI

from backend.api.routes import router

app = FastAPI(title="PPT-Agent", version="0.1.0")
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok"}

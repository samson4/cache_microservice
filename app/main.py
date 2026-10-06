from fastapi import FastAPI

from app.cache.router import cache_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(cache_router, tags=["payloads"])

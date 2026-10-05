from fastapi import APIRouter, FastAPI

from app.cache.router import cache_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json"
)

global_router = APIRouter(prefix=settings.API_V1_PREFIX, tags=["global"])


@app.get("/")
def read_root():
    return {"Hello": "World"}



@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(cache_router, prefix=f"{settings.API_V1_PREFIX}/cache", tags=["cache"])
app.include_router(global_router, prefix=settings.API_V1_PREFIX, tags=["global"])

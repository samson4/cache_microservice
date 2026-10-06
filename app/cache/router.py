from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.cache.schemas import CacheCreateResponse, CacheInput, CacheRead
from app.cache.service import CacheBusyError, PayloadNotFoundError, cache_service
from app.core.db import get_db

cache_router = APIRouter()


@cache_router.post("/payload", response_model=CacheCreateResponse)
def create_cache_route(payload: CacheInput, db: Session = Depends(get_db)):
    try:
        return cache_service.create_cache(db, payload)
    except CacheBusyError as error:
        raise HTTPException(
            status_code=503,
            detail="Cache is busy; retry later",
            headers={"Retry-After": "1"},
        ) from error


@cache_router.get("/payload/{id}", response_model=CacheRead)
def get_cache_route(id: str, db: Session = Depends(get_db)):
    try:
        return cache_service.get_cache(db, id)
    except PayloadNotFoundError as error:
        raise HTTPException(status_code=404, detail="Payload not found") from error

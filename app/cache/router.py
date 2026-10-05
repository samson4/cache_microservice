from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.cache.schemas import CacheCreateResponse, CacheInput, CacheRead
from app.cache.service import cache_service
from app.core.db import get_db

cache_router = APIRouter()



@cache_router.post("/payload", response_model=CacheCreateResponse)
def create_cache_route(payload: CacheInput, db: Session = Depends(get_db)):
   
    return cache_service.create_cache(db, payload)


@cache_router.get("/payload/{id}", response_model=CacheRead)
def get_cache_route(id: str, db: Session = Depends(get_db)):
    return cache_service.get_cache(db, id)
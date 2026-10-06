from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.cache.router import cache_router
from app.core.config import settings
from app.core.db import get_db

app = FastAPI(
    title=settings.APP_NAME,
)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get(
    "/health",
    responses={503: {"description": "Database unavailable"}},
)
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        ) from error
    return {"status": "ok"}


app.include_router(cache_router, tags=["payloads"])

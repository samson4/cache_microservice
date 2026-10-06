import json

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.cache.models import Cache, PayloadCache
from app.cache.schemas import CacheInput


class CacheBusyError(Exception):
    """Raised when SQLite cannot obtain its writer lock in time."""


class CacheService:
    def __init__(self):
        pass

    def _serialize_request(self, cache_input: CacheInput) -> str:
        return json.dumps(
            cache_input.model_dump(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

    def _begin_write(self, db: Session) -> None:
        if db.bind is not None and db.bind.dialect.name == "sqlite":
            db.execute(text("BEGIN IMMEDIATE"))

    @staticmethod
    def _is_lock_timeout(error: OperationalError) -> bool:
        return "locked" in str(error.orig).lower()

    def _get_or_transform(self, db: Session, input_text: str) -> str:
        cached_transformation = (
            db.query(Cache).filter(Cache.input_text == input_text).first()
        )

        if cached_transformation is not None:
            return cached_transformation.output_text

        output_text = self._transformer(input_text)

        db.add(
            Cache(
                input_text=input_text,
                output_text=output_text,
            )
        )
        db.flush()
        return output_text

    def create_cache(self, db: Session, cache_input: CacheInput) -> dict:
        try:
            self._begin_write(db)
            request_data = self._serialize_request(cache_input)
            cache_result = (
                db.query(PayloadCache)
                .filter(PayloadCache.request_data == request_data)
                .first()
            )

            if cache_result:
                db.commit()
                return {"id": cache_result.id}

            output_parts: list[str] = []
            for first, second in zip(
                cache_input.list_1,
                cache_input.list_2,
                strict=True,
            ):
                output_parts.append(self._get_or_transform(db, first))
                output_parts.append(self._get_or_transform(db, second))

            payload_cache = PayloadCache(
                request_data=request_data,
                output=", ".join(output_parts),
            )
            db.add(payload_cache)
            db.commit()
            db.refresh(payload_cache)
            return {"id": payload_cache.id}
        except OperationalError as error:
            db.rollback()
            if self._is_lock_timeout(error):
                raise CacheBusyError from error
            raise
        except Exception:
            db.rollback()
            raise

    def get_cache(self, db: Session, cache_id: str) -> PayloadCache:
        query = db.query(PayloadCache).filter(PayloadCache.id == cache_id)

        result = query.first()
        if result is None:
            raise HTTPException(status_code=404, detail="Payload not found")

        return result

    # here I was assuming that the transformer function would transform the entire input lists into a single string
    # def _transformer(self, cache_input: CacheInput)-> str:
    #     list_3 : list[str] = []
    #     for i,j in zip(cache_input.list_1, cache_input.list_2):
    #         list_3.append(i.upper())
    #         list_3.append(j.upper())

    #     return ", ".join(list_3)
    def _transformer(self, input_text: str) -> str:

        return input_text.upper()


cache_service = CacheService()

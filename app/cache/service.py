import json
from fastapi import HTTPException
from app.cache.schemas import CacheInput
from sqlalchemy.orm import Session

from app.cache.models import Cache, PayloadCache

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
    def create_cache(self, db: Session, cache_input: CacheInput) -> dict:
        request_data = self._serialize_request(cache_input)
        # first layer of caching: check if the request_data already exists in the database
        cache_result = db.query(PayloadCache).filter(PayloadCache.request_data == request_data).first()
        
        if cache_result:
            return {"id": cache_result.id}
        if not len(cache_input.list_1) == len(cache_input.list_2):
            raise HTTPException(status_code=400, detail="Input lists must have the same length")
        for i, j in zip(cache_input.list_1, cache_input.list_2):
           pass
            


    def get_cache(self, db: Session, cache_id: int) -> PayloadCache:
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

    def _transformer(self, str_input: str) -> str:
        
        return str_input.upper()


cache_service = CacheService()    
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
        request_data = self._serialize_request(cache_input)
        # first layer of caching: check if the request_data already exists in the database
        cache_result = db.query(PayloadCache).filter(PayloadCache.request_data == request_data).first()
        
        if cache_result:
            return {"id": cache_result.id}
        output_parts: list[str] = []    
        for i, j in zip(cache_input.list_1, cache_input.list_2):
           output_parts.append(self._get_or_transform(db, i))
           output_parts.append(self._get_or_transform(db, j))
        output_text = ", ".join(output_parts)
        # second layer of caching: store the request_data and output_text in the database
        payload_cache = PayloadCache(request_data=request_data, output=output_text)
        db.add(payload_cache)
        db.commit()
        db.refresh(payload_cache)
        return {"id": payload_cache.id}
            


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
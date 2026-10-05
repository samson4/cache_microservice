from typing import Optional

from pydantic import BaseModel, Field



class CacheBase(BaseModel):
    pass


class CacheInput(CacheBase):
    list_1: list[str] 
    list_2: list[str]


class CacheCreate(CacheBase):
    lists: CacheInput 

class CacheCreateResponse(CacheBase):
    id: int
    model_config = {"from_attributes": True} 

class CacheRead(CacheBase):
    
    output: str
    model_config = {"from_attributes": True}         
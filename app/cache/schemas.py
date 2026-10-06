from typing import Self

from pydantic import BaseModel, model_validator


class CacheBase(BaseModel):
    pass


class CacheInput(CacheBase):
    list_1: list[str]
    list_2: list[str]

    @model_validator(mode="after")
    def validate_equal_lengths(self) -> Self:
        if len(self.list_1) != len(self.list_2):
            raise ValueError("Input lists must have the same length")
        return self


class CacheCreate(CacheBase):
    lists: CacheInput


class CacheCreateResponse(CacheBase):
    id: str
    model_config = {"from_attributes": True}


class CacheRead(CacheBase):
    output: str
    model_config = {"from_attributes": True}

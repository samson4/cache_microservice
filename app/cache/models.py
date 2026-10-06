from sqlalchemy import Column, String, Text

from app.core.base import Base
from app.mixins.id import UniqueIDMixin
from app.mixins.timestamp import TimestampMixin


class Cache(Base, UniqueIDMixin, TimestampMixin):
    __tablename__ = "transformation_cache"
    input_text = Column(String, nullable=False, unique=True)
    output_text = Column(String, nullable=False)


class PayloadCache(Base, UniqueIDMixin, TimestampMixin):
    __tablename__ = "payload_cache"
    request_data = Column(Text, nullable=False, unique=True)
    output = Column(String, nullable=False)

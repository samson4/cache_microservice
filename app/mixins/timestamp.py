from datetime import UTC, datetime

from sqlalchemy import Column, DateTime
from sqlalchemy.orm import declarative_mixin


def utc_now() -> datetime:
    return datetime.now(UTC)


@declarative_mixin
class TimestampMixin:
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

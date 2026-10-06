from datetime import UTC, datetime

from sqlalchemy import Column, DateTime


def utc_now() -> datetime:
    return datetime.now(UTC)


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

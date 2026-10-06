import uuid

from sqlalchemy import Column, String


class UniqueIDMixin:
    """
    Mixin to add a unique ID to a SQLAlchemy model.
    """

    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))

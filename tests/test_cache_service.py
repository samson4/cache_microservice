import unittest
from unittest.mock import patch

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.cache.models import Cache
from app.cache.schemas import CacheInput
from app.cache.service import CacheService
from app.core.base import Base


class CacheServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
        )
        Base.metadata.create_all(self.engine)
        self.db = session_factory()
        self.service = CacheService()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def test_creates_and_reads_interleaved_payload(self) -> None:
        cache_input = CacheInput(
            list_1=["first string", "second string", "third string"],
            list_2=["other string", "another string", "last string"],
        )

        created = self.service.create_cache(self.db, cache_input)
        payload = self.service.get_cache(self.db, created["id"])

        self.assertEqual(
            payload.output,
            "FIRST STRING, OTHER STRING, SECOND STRING, "
            "ANOTHER STRING, THIRD STRING, LAST STRING",
        )

    def test_reuses_transformations_and_payload_identifier(self) -> None:
        first_input = CacheInput(
            list_1=["shared", "shared"],
            list_2=["other", "shared"],
        )

        with patch.object(
            self.service,
            "_transformer",
            wraps=self.service._transformer,
        ) as transformer:
            first = self.service.create_cache(self.db, first_input)
            repeated = self.service.create_cache(self.db, first_input)
            self.service.create_cache(
                self.db,
                CacheInput(list_1=["shared"], list_2=["new"]),
            )

        self.assertEqual(first["id"], repeated["id"])
        self.assertEqual(transformer.call_count, 3)
        self.assertEqual(
            self.db.scalar(select(func.count()).select_from(Cache)),
            3,
        )

    def test_rejects_lists_with_different_lengths(self) -> None:
        with self.assertRaises(ValidationError):
            CacheInput(list_1=["one"], list_2=[])

    def test_missing_payload_raises_not_found(self) -> None:
        with self.assertRaises(HTTPException) as error:
            self.service.get_cache(self.db, "missing-id")

        self.assertEqual(error.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.cache.service import CacheService
from app.core.base import Base
from app.core.db import get_db
from app.main import app


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine, autoflush=False)
        self.service = CacheService()

        def test_database():
            db = self.session_factory()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = test_database
        self.service_patch = patch("app.cache.router.cache_service", self.service)
        self.service_patch.start()
        self.client_context = TestClient(app)
        self.client = self.client_context.__enter__()

    def tearDown(self) -> None:
        self.client_context.__exit__(None, None, None)
        self.service_patch.stop()
        app.dependency_overrides.clear()
        self.engine.dispose()

    def test_creates_and_reads_sample_payload(self) -> None:
        response = self.client.post(
            "/payload",
            json={
                "list_1": ["first string", "second string", "third string"],
                "list_2": ["other string", "another string", "last string"],
            },
        )

        self.assertEqual(response.status_code, 200)
        payload_id = response.json()["id"]
        read = self.client.get(f"/payload/{payload_id}")
        self.assertEqual(read.status_code, 200)
        self.assertEqual(
            read.json(),
            {
                "output": "FIRST STRING, OTHER STRING, SECOND STRING, "
                "ANOTHER STRING, THIRD STRING, LAST STRING"
            },
        )

    def test_reuses_payload_and_only_transforms_cache_misses(self) -> None:
        first_body = {"list_1": ["shared", "shared"], "list_2": ["other", "shared"]}
        second_body = {"list_1": ["shared"], "list_2": ["new"]}

        with patch.object(
            self.service,
            "_transformer",
            wraps=self.service._transformer,
        ) as transformer:
            first = self.client.post("/payload", json=first_body)
            repeated = self.client.post("/payload", json=first_body)
            partial_hit = self.client.post("/payload", json=second_body)

        self.assertEqual(first.json()["id"], repeated.json()["id"])
        self.assertNotEqual(first.json()["id"], partial_hit.json()["id"])
        self.assertEqual(transformer.call_count, 3)

    def test_validation_missing_payload_and_health(self) -> None:
        invalid = self.client.post(
            "/payload",
            json={"list_1": ["one"], "list_2": []},
        )
        missing = self.client.get("/payload/missing-id")

        self.assertEqual(invalid.status_code, 422)
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(missing.json(), {"detail": "Payload not found"})
        self.assertEqual(self.client.get("/health").json(), {"status": "ok"})
        self.assertEqual(
            self.client.post(
                "/api/v1/cache/payload",
                json={"list_1": ["one"], "list_2": ["two"]},
            ).status_code,
            404,
        )


if __name__ == "__main__":
    unittest.main()

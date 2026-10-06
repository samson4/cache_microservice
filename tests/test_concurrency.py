import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.cache.schemas import CacheInput
from app.cache.service import CacheBusyError, CacheService
from app.core.base import Base


class ConcurrencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        database_path = Path(self.temporary_directory.name) / "cache.db"
        database_url = f"sqlite:///{database_path}"
        connect_args = {"check_same_thread": False, "timeout": 2}
        self.engines = [
            create_engine(database_url, connect_args=connect_args),
            create_engine(database_url, connect_args=connect_args),
        ]
        Base.metadata.create_all(self.engines[0])
        self.session_factories = [
            sessionmaker(bind=engine, autoflush=False) for engine in self.engines
        ]
        self.service = CacheService()

    def tearDown(self) -> None:
        for engine in self.engines:
            engine.dispose()
        self.temporary_directory.cleanup()

    def _create_simultaneously(self, requests):
        barrier = threading.Barrier(len(requests))

        def create(index):
            barrier.wait(timeout=5)
            with self.session_factories[index]() as session:
                return self.service.create_cache(session, requests[index])["id"]

        with ThreadPoolExecutor(max_workers=len(requests)) as executor:
            return list(executor.map(create, range(len(requests))))

    def test_identical_requests_transform_each_string_once(self) -> None:
        request = CacheInput(list_1=["shared"], list_2=["other"])
        calls = []
        calls_lock = threading.Lock()

        def slow_transformer(value):
            with calls_lock:
                calls.append(value)
            time.sleep(0.05)
            return value.upper()

        with patch.object(self.service, "_transformer", side_effect=slow_transformer):
            identifiers = self._create_simultaneously([request, request])

        self.assertEqual(len(set(identifiers)), 1)
        self.assertCountEqual(calls, ["shared", "other"])

    def test_overlapping_requests_reuse_the_shared_transformation(self) -> None:
        requests = [
            CacheInput(list_1=["shared"], list_2=["first"]),
            CacheInput(list_1=["shared"], list_2=["second"]),
        ]
        calls = []
        calls_lock = threading.Lock()

        def slow_transformer(value):
            with calls_lock:
                calls.append(value)
            time.sleep(0.05)
            return value.upper()

        with patch.object(self.service, "_transformer", side_effect=slow_transformer):
            identifiers = self._create_simultaneously(requests)

        self.assertEqual(len(set(identifiers)), 2)
        self.assertCountEqual(calls, ["shared", "first", "second"])

    def test_transformer_failure_rolls_back_and_releases_lock(self) -> None:
        request = CacheInput(list_1=["one"], list_2=["two"])

        with self.session_factories[0]() as session:
            with (
                patch.object(
                    self.service,
                    "_transformer",
                    side_effect=RuntimeError("transformer failed"),
                ),
                self.assertRaises(RuntimeError),
            ):
                self.service.create_cache(session, request)

            created = self.service.create_cache(session, request)
            self.assertEqual(
                self.service.get_cache(session, created["id"]).output,
                "ONE, TWO",
            )

    def test_writer_timeout_raises_cache_busy_error(self) -> None:
        short_timeout_engine = create_engine(
            self.engines[1].url,
            connect_args={"check_same_thread": False, "timeout": 0.05},
        )
        short_timeout_session = sessionmaker(
            bind=short_timeout_engine,
            autoflush=False,
        )

        try:
            with (
                self.engines[0].connect() as locked_connection,
                short_timeout_session() as session,
            ):
                locked_connection.exec_driver_sql("BEGIN IMMEDIATE")
                with self.assertRaises(CacheBusyError):
                    self.service.create_cache(
                        session,
                        CacheInput(list_1=["one"], list_2=["two"]),
                    )
                locked_connection.rollback()
        finally:
            short_timeout_engine.dispose()


if __name__ == "__main__":
    unittest.main()

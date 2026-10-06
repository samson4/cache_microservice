import unittest
from datetime import UTC

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.cache.models import Cache
from app.core.base import Base
from app.mixins.timestamp import utc_now


class TimestampTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def test_timestamp_defaults_are_callable_and_generate_utc_values(self) -> None:
        created_at = Cache.__table__.c.created_at
        updated_at = Cache.__table__.c.updated_at

        self.assertTrue(created_at.default.is_callable)
        self.assertTrue(updated_at.default.is_callable)
        self.assertTrue(updated_at.onupdate.is_callable)
        self.assertEqual(utc_now().tzinfo, UTC)

    def test_timestamps_are_generated_per_row_and_updated_on_change(self) -> None:
        first = Cache(input_text="first", output_text="FIRST")
        self.session.add(first)
        self.session.flush()

        second = Cache(input_text="second", output_text="SECOND")
        self.session.add(second)
        self.session.flush()

        self.assertIsNotNone(first.created_at)
        self.assertIsNotNone(first.updated_at)
        self.assertNotEqual(first.created_at, second.created_at)

        previous_updated_at = first.updated_at
        first.output_text = "CHANGED"
        self.session.flush()

        self.assertGreater(first.updated_at, previous_updated_at)


if __name__ == "__main__":
    unittest.main()

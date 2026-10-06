import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect

from alembic import command


class MigrationTests(unittest.TestCase):
    def test_upgrade_head_builds_current_schema_from_empty_database(self) -> None:
        project_root = Path(__file__).resolve().parents[1]

        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "migration-test.db"
            database_url = f"sqlite:///{database_path}"
            config = Config(project_root / "alembic.ini")
            config.attributes["database_url"] = database_url

            command.upgrade(config, "head")

            engine = create_engine(database_url)
            try:
                inspector = inspect(engine)
                self.assertEqual(
                    set(inspector.get_table_names()),
                    {"alembic_version", "payload_cache", "transformation_cache"},
                )
                self.assertIn(
                    "request_data",
                    {
                        column["name"]
                        for column in inspector.get_columns("payload_cache")
                    },
                )

                with engine.connect() as connection:
                    migration_context = MigrationContext.configure(connection)
                    self.assertEqual(
                        migration_context.get_current_revision(),
                        ScriptDirectory.from_config(config).get_current_head(),
                    )
            finally:
                engine.dispose()


if __name__ == "__main__":
    unittest.main()

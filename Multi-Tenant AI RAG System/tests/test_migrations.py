"""
Test Alembic migration round-trips: upgrade all → downgrade all → upgrade all.
Verifies that all migrations can be applied and reverted cleanly.
"""
import os
import pytest
from pathlib import Path

from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text


# Use a dedicated temporary SQLite database for migration tests
_TEST_DB = "./test_migrations.db"
_TEST_DB_URL = f"sqlite:///{_TEST_DB}"


# ---------------------------------------------------------------------------
# Neutralise the global conftest.py `setup_db` autouse fixture so it does NOT
# call Base.metadata.create_all() before our Alembic-driven tests.  That
# fixture pre-creates every table, which would cause "table already exists"
# errors when the first migration tries to run.
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def setup_db():  # noqa: F811 — intentional override of conftest fixture
    """No-op: migration tests manage the schema themselves via Alembic."""
    yield


@pytest.fixture(autouse=True)
def clean_migration_db():
    """Ensure a clean database and correct DATABASE_URL for each migration test.

    alembic/env.py calls ``config.set_main_option("sqlalchemy.url",
    settings.database_url)`` which would override the URL we pass via
    ``Config.set_main_option``.  Patching the env var (and the already-loaded
    settings object) guarantees env.py reads the test DB URL.
    """
    import app.config as _cfg_module

    # Remove any existing test DB
    if os.path.exists(_TEST_DB):
        os.remove(_TEST_DB)

    # Patch the environment variable and the live settings object so that
    # alembic/env.py picks up the test DB URL when it calls
    # settings.database_url.
    original_env = os.environ.get("DATABASE_URL")
    original_settings_url = _cfg_module.settings.database_url

    os.environ["DATABASE_URL"] = _TEST_DB_URL
    _cfg_module.settings.database_url = _TEST_DB_URL

    yield

    # Restore original values
    if original_env is None:
        os.environ.pop("DATABASE_URL", None)
    else:
        os.environ["DATABASE_URL"] = original_env
    _cfg_module.settings.database_url = original_settings_url

    # Cleanup test DB file
    if os.path.exists(_TEST_DB):
        os.remove(_TEST_DB)


def _get_alembic_config() -> Config:
    """Create an Alembic config pointing to the test database."""
    # Find the project root (where alembic.ini lives)
    project_root = Path(__file__).resolve().parent.parent
    ini_path = project_root / "alembic.ini"

    cfg = Config(str(ini_path))
    cfg.set_main_option("sqlalchemy.url", _TEST_DB_URL)
    return cfg


class TestMigrationRoundTrip:
    def test_upgrade_to_head(self):
        """All migrations can be applied from base to head."""
        cfg = _get_alembic_config()
        command.upgrade(cfg, "head")

        # Verify tables were created
        engine = create_engine(_TEST_DB_URL)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        engine.dispose()

        # Check that core tables exist
        assert "tenants" in tables
        assert "users" in tables
        assert "documents" in tables
        assert "chat_messages" in tables
        assert "audit_logs" in tables
        assert "alembic_version" in tables

    def test_downgrade_to_base(self):
        """All migrations can be reverted from head to base."""
        cfg = _get_alembic_config()

        # First upgrade to head
        command.upgrade(cfg, "head")

        # Then downgrade to base
        command.downgrade(cfg, "base")

        # Verify all tables are gone (except alembic_version)
        engine = create_engine(_TEST_DB_URL)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        engine.dispose()

        # Only alembic_version should remain (or nothing)
        app_tables = [t for t in tables if t != "alembic_version"]
        assert app_tables == [], f"Tables still present after downgrade: {app_tables}"

    def test_full_round_trip(self):
        """Upgrade → downgrade → upgrade cycle completes cleanly."""
        cfg = _get_alembic_config()

        # Upgrade to head
        command.upgrade(cfg, "head")

        # Downgrade to base
        command.downgrade(cfg, "base")

        # Upgrade again
        command.upgrade(cfg, "head")

        # Verify final state has all tables
        engine = create_engine(_TEST_DB_URL)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        engine.dispose()

        assert "tenants" in tables
        assert "users" in tables
        assert "documents" in tables
        assert "api_keys" in tables
        assert "blacklisted_tokens" in tables

    def test_step_by_step_upgrade(self):
        """Each migration can be applied individually in sequence."""
        cfg = _get_alembic_config()
        script_dir = ScriptDirectory.from_config(cfg)

        # walk_revisions() yields head → base; reverse to get base → head order
        revisions = [rev.revision for rev in script_dir.walk_revisions()]
        revisions.reverse()  # Now in base→head order

        # Apply each one individually
        for rev in revisions:
            command.upgrade(cfg, rev)

        # Verify we're at head
        engine = create_engine(_TEST_DB_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            current = result.scalar()
        engine.dispose()

        assert current == revisions[-1], f"Expected head={revisions[-1]}, got {current}"

    def test_step_by_step_downgrade(self):
        """Each migration can be reverted individually in reverse order."""
        cfg = _get_alembic_config()
        script_dir = ScriptDirectory.from_config(cfg)

        # First upgrade to head
        command.upgrade(cfg, "head")

        # walk_revisions() yields head → base order — exactly what we need
        revisions = list(script_dir.walk_revisions())

        # Downgrade one step at a time
        for i, rev in enumerate(revisions):
            if rev.down_revision:
                target = rev.down_revision if isinstance(rev.down_revision, str) else rev.down_revision[0]
                command.downgrade(cfg, target)
            else:
                # This is the first migration — downgrade to base
                command.downgrade(cfg, "base")

        # Verify we're at base
        engine = create_engine(_TEST_DB_URL)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        engine.dispose()

        app_tables = [t for t in tables if t != "alembic_version"]
        assert app_tables == [], f"Tables still present: {app_tables}"

    def test_current_matches_head(self):
        """After upgrading, current revision matches head."""
        cfg = _get_alembic_config()
        script_dir = ScriptDirectory.from_config(cfg)

        command.upgrade(cfg, "head")

        head = script_dir.get_current_head()

        engine = create_engine(_TEST_DB_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            current = result.scalar()
        engine.dispose()

        assert current == head

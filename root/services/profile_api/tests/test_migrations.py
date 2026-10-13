from pathlib import Path
import os
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from profile_api.models import Account, Profile, ProfileRevision, utc_now


SERVICE_ROOT = Path(__file__).resolve().parents[1]
POSTGRES_MIGRATION_URL = os.environ.get("PROFILE_API_MIGRATION_TEST_DATABASE_URL")


def test_initial_migration_up_and_down_from_clean_database(tmp_path):
    database_path = tmp_path / "migration.sqlite3"
    config = Config(str(SERVICE_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(SERVICE_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")

    command.upgrade(config, "head")
    engine = create_engine(f"sqlite:///{database_path}")
    assert {
        "accounts",
        "account_sessions",
        "linked_identities",
        "profiles",
        "profile_revisions",
        "entitlements",
        "alembic_version",
    }.issubset(set(inspect(engine).get_table_names()))

    now = utc_now()
    account_id = uuid4()
    profile_id = uuid4()
    with Session(engine) as session:
        session.add_all(
            (
                Account(id=account_id, status="active", created_at=now, updated_at=now),
                Profile(
                    id=profile_id,
                    account_id=account_id,
                    current_revision=1,
                    status="active",
                    created_at=now,
                    updated_at=now,
                ),
                ProfileRevision(
                    profile_id=profile_id,
                    revision=1,
                    base_revision=None,
                    client_save_id=uuid4(),
                    device_id=None,
                    payload={"schema_version": 8},
                    payload_sha256="a" * 64,
                    created_at=now,
                ),
            )
        )
        session.commit()
        with pytest.raises(IntegrityError, match="profile revisions are immutable"):
            session.query(ProfileRevision).filter_by(profile_id=profile_id).update(
                {ProfileRevision.payload_sha256: "b" * 64}
            )
            session.commit()
        session.rollback()
        with pytest.raises(IntegrityError, match="profile revisions are immutable"):
            session.query(ProfileRevision).filter_by(profile_id=profile_id).delete()
            session.commit()
        session.rollback()

    command.downgrade(config, "base")

    assert inspect(engine).get_table_names() == ["alembic_version"]
    engine.dispose()


@pytest.mark.skipif(
    not POSTGRES_MIGRATION_URL
    or not POSTGRES_MIGRATION_URL.startswith(
        ("postgresql://", "postgresql+psycopg://")
    ),
    reason="requires a dedicated clean PostgreSQL PROFILE_API_MIGRATION_TEST_DATABASE_URL",
)
def test_postgres_migration_up_down_and_immutable_revision_triggers():
    config = Config(str(SERVICE_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(SERVICE_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", POSTGRES_MIGRATION_URL)
    engine = create_engine(POSTGRES_MIGRATION_URL)

    command.upgrade(config, "head")
    assert {
        "accounts",
        "account_sessions",
        "linked_identities",
        "profiles",
        "profile_revisions",
        "entitlements",
    }.issubset(set(inspect(engine).get_table_names()))

    now = utc_now()
    account_id = uuid4()
    profile_id = uuid4()
    with Session(engine) as session:
        session.add_all(
            (
                Account(id=account_id, status="active", created_at=now, updated_at=now),
                Profile(
                    id=profile_id,
                    account_id=account_id,
                    current_revision=1,
                    status="active",
                    created_at=now,
                    updated_at=now,
                ),
                ProfileRevision(
                    profile_id=profile_id,
                    revision=1,
                    base_revision=None,
                    client_save_id=uuid4(),
                    device_id=None,
                    payload={"schema_version": 8},
                    payload_sha256="a" * 64,
                    created_at=now,
                ),
            )
        )
        session.commit()
        with pytest.raises(SQLAlchemyError, match="profile revisions are immutable"):
            session.query(ProfileRevision).filter_by(profile_id=profile_id).update(
                {ProfileRevision.payload_sha256: "b" * 64}
            )
            session.commit()
        session.rollback()
        with pytest.raises(SQLAlchemyError, match="profile revisions are immutable"):
            session.query(ProfileRevision).filter_by(profile_id=profile_id).delete()
            session.commit()
        session.rollback()

    command.downgrade(config, "base")
    assert not {
        "accounts",
        "account_sessions",
        "linked_identities",
        "profiles",
        "profile_revisions",
        "entitlements",
    }.intersection(set(inspect(engine).get_table_names()))
    engine.dispose()

"""Create DD account, session, profile, revision, identity, and entitlement tables."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0001_profile_service"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


UUID = sa.Uuid(as_uuid=True)
JSON_DOCUMENT = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status in ('active', 'disabled')", name="ck_accounts_status"),
    )
    op.create_table(
        "account_sessions",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("account_id", UUID, nullable=False),
        sa.Column("access_token_hash", sa.String(length=64), nullable=False),
        sa.Column("refresh_token_hash", sa.String(length=64), nullable=False),
        sa.Column("device_id", UUID, nullable=False),
        sa.Column("access_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("refresh_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("access_token_hash", name="uq_sessions_access_token_hash"),
        sa.UniqueConstraint("refresh_token_hash", name="uq_sessions_refresh_token_hash"),
    )
    op.create_index("ix_sessions_account_id", "account_sessions", ["account_id"])
    op.create_table(
        "linked_identities",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("account_id", UUID, nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_subject", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("provider", "provider_subject", name="uq_identity_provider_subject"),
    )
    op.create_index("ix_linked_identities_account_id", "linked_identities", ["account_id"])
    op.create_table(
        "profiles",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("account_id", UUID, nullable=False),
        sa.Column("current_revision", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status in ('active', 'deleted')", name="ck_profiles_status"),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_profiles_account_created", "profiles", ["account_id", "created_at", "id"]
    )
    op.create_table(
        "profile_revisions",
        sa.Column("profile_id", UUID, nullable=False),
        sa.Column("revision", sa.BigInteger(), nullable=False),
        sa.Column("base_revision", sa.BigInteger(), nullable=True),
        sa.Column("client_save_id", UUID, nullable=False),
        sa.Column("device_id", UUID, nullable=True),
        sa.Column("payload", JSON_DOCUMENT, nullable=False),
        sa.Column("payload_sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("revision > 0", name="ck_revision_positive"),
        sa.CheckConstraint(
            "base_revision is null or base_revision > 0", name="ck_revision_base_positive"
        ),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("profile_id", "revision"),
        sa.UniqueConstraint("profile_id", "client_save_id", name="uq_revision_client_save"),
    )
    op.create_index(
        "ix_profile_revisions_created_at", "profile_revisions", ["profile_id", "created_at"]
    )
    op.create_table(
        "entitlements",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("account_id", UUID, nullable=False),
        sa.Column("product_key", sa.String(length=128), nullable=False),
        sa.Column("source_provider", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", JSON_DOCUMENT, nullable=False),
        sa.CheckConstraint(
            "status in ('active', 'expired', 'revoked')", name="ck_entitlements_status"
        ),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_entitlements_account_granted", "entitlements", ["account_id", "granted_at"]
    )
    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            """
            CREATE FUNCTION dd_reject_profile_revision_mutation() RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'profile revisions are immutable';
            END;
            $$ LANGUAGE plpgsql
            """
        )
        op.execute(
            """
            CREATE TRIGGER trg_profile_revisions_immutable
            BEFORE UPDATE OR DELETE ON profile_revisions
            FOR EACH ROW EXECUTE FUNCTION dd_reject_profile_revision_mutation()
            """
        )
    elif op.get_bind().dialect.name == "sqlite":
        op.execute(
            """
            CREATE TRIGGER trg_profile_revisions_no_update
            BEFORE UPDATE ON profile_revisions
            BEGIN
                SELECT RAISE(ABORT, 'profile revisions are immutable');
            END
            """
        )
        op.execute(
            """
            CREATE TRIGGER trg_profile_revisions_no_delete
            BEFORE DELETE ON profile_revisions
            BEGIN
                SELECT RAISE(ABORT, 'profile revisions are immutable');
            END
            """
        )


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TRIGGER trg_profile_revisions_immutable ON profile_revisions")
        op.execute("DROP FUNCTION dd_reject_profile_revision_mutation()")
    elif op.get_bind().dialect.name == "sqlite":
        op.execute("DROP TRIGGER trg_profile_revisions_no_delete")
        op.execute("DROP TRIGGER trg_profile_revisions_no_update")
    op.drop_index("ix_entitlements_account_granted", table_name="entitlements")
    op.drop_table("entitlements")
    op.drop_index("ix_profile_revisions_created_at", table_name="profile_revisions")
    op.drop_table("profile_revisions")
    op.drop_index("ix_profiles_account_created", table_name="profiles")
    op.drop_table("profiles")
    op.drop_index("ix_linked_identities_account_id", table_name="linked_identities")
    op.drop_table("linked_identities")
    op.drop_index("ix_sessions_account_id", table_name="account_sessions")
    op.drop_table("account_sessions")
    op.drop_table("accounts")

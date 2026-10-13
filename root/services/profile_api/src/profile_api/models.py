from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    String,
    Uuid,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from profile_api.database import Base


JSON_DOCUMENT = JSON().with_variant(JSONB(), "postgresql")


def utc_now():
    return datetime.now(timezone.utc)


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint("status in ('active', 'disabled')", name="ck_accounts_status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )


class AccountSession(Base):
    __tablename__ = "account_sessions"
    __table_args__ = (
        UniqueConstraint("access_token_hash", name="uq_sessions_access_token_hash"),
        UniqueConstraint("refresh_token_hash", name="uq_sessions_refresh_token_hash"),
        Index("ix_sessions_account_id", "account_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    account_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    access_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    refresh_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    device_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    access_expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    refresh_expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )


class LinkedIdentity(Base):
    __tablename__ = "linked_identities"
    __table_args__ = (
        UniqueConstraint("provider", "provider_subject", name="uq_identity_provider_subject"),
        Index("ix_linked_identities_account_id", "account_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    account_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_subject: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = (
        CheckConstraint("status in ('active', 'deleted')", name="ck_profiles_status"),
        Index("ix_profiles_account_created", "account_id", "created_at", "id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    account_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    current_revision: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )


class ProfileRevision(Base):
    __tablename__ = "profile_revisions"
    __table_args__ = (
        UniqueConstraint("profile_id", "client_save_id", name="uq_revision_client_save"),
        CheckConstraint("revision > 0", name="ck_revision_positive"),
        CheckConstraint(
            "base_revision is null or base_revision > 0", name="ck_revision_base_positive"
        ),
        Index("ix_profile_revisions_created_at", "profile_id", "created_at"),
    )

    profile_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True
    )
    revision: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    base_revision: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    client_save_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    device_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON_DOCUMENT, nullable=False)
    payload_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )


class Entitlement(Base):
    __tablename__ = "entitlements"
    __table_args__ = (
        CheckConstraint(
            "status in ('active', 'expired', 'revoked')", name="ck_entitlements_status"
        ),
        Index("ix_entitlements_account_granted", "account_id", "granted_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    account_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    product_key: Mapped[str] = mapped_column(String(128), nullable=False)
    source_provider: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON_DOCUMENT, nullable=False, default=dict
    )

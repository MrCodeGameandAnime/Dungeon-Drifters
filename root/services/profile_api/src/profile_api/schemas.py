from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator


class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ResponseModel(BaseModel):
    model_config = ConfigDict(strict=True)


def _canonical_uuid(value):
    if not isinstance(value, str):
        raise ValueError("UUID must be a canonical lowercase string")
    try:
        parsed = UUID(value)
    except (ValueError, AttributeError) as error:
        raise ValueError("UUID must be a canonical lowercase string") from error
    if str(parsed) != value:
        raise ValueError("UUID must be a canonical lowercase string")
    return parsed


class AnonymousAccountRequest(RequestModel):
    device_id: UUID

    @field_validator("device_id", mode="before")
    @classmethod
    def validate_device_id(cls, value):
        return _canonical_uuid(value)


class RefreshRequest(RequestModel):
    refresh_token: str = Field(min_length=1, max_length=512)


class CreateProfileRequest(RequestModel):
    profile_id: UUID
    client_save_id: UUID
    device_id: UUID
    payload: dict[str, Any]

    @field_validator("profile_id", "client_save_id", "device_id", mode="before")
    @classmethod
    def validate_uuids(cls, value):
        return _canonical_uuid(value)


class ProgressionRequest(RequestModel):
    base_revision: StrictInt = Field(gt=0)
    client_save_id: UUID
    device_id: UUID
    payload: dict[str, Any]

    @field_validator("client_save_id", "device_id", mode="before")
    @classmethod
    def validate_uuids(cls, value):
        return _canonical_uuid(value)


class HealthResponse(ResponseModel):
    status: str
    api_version: str


class AnonymousAccountResponse(ResponseModel):
    account_id: str
    access_token: str
    access_expires_at: str
    refresh_token: str
    refresh_expires_at: str


class RefreshResponse(ResponseModel):
    access_token: str
    access_expires_at: str


class RevisionResponse(ResponseModel):
    revision: int
    base_revision: int | None
    client_save_id: str
    device_id: str | None
    payload_sha256: str
    created_at: str
    payload: dict[str, Any]


class ProfileResponse(ResponseModel):
    profile_id: str
    account_id: str
    current_revision: int
    head: RevisionResponse
    created_revision: int | None = None
    accepted_revision: int | None = None


class ProfileListItemResponse(ResponseModel):
    profile_id: str
    current_revision: int
    created_at: str
    updated_at: str


class ProfileListResponse(ResponseModel):
    profiles: list[ProfileListItemResponse]


class EntitlementResponse(ResponseModel):
    id: str
    product_key: str
    source_provider: str
    status: str
    granted_at: str
    expires_at: str | None
    revoked_at: str | None
    metadata: dict[str, Any]


class EntitlementListResponse(ResponseModel):
    entitlements: list[EntitlementResponse]

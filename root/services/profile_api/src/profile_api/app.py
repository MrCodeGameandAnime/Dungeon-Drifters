from datetime import timezone
import hashlib
import secrets
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

from profile_api.config import Settings
from profile_api.errors import (
    APIError,
    api_error_handler,
    http_error_handler,
    internal_error_handler,
    request_validation_handler,
)
from profile_api.models import (
    Account,
    AccountSession,
    Entitlement,
    Profile,
    ProfileRevision,
    utc_now,
)
from profile_api.save_contract import InvalidPayload, normalize_and_digest
from profile_api.schemas import (
    AnonymousAccountRequest,
    AnonymousAccountResponse,
    CreateProfileRequest,
    EntitlementListResponse,
    HealthResponse,
    ProfileListResponse,
    ProfileResponse,
    ProgressionRequest,
    RefreshResponse,
    RefreshRequest,
)


bearer_scheme = HTTPBearer(auto_error=False)


def _token_hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _new_token():
    return secrets.token_urlsafe(32)


def _aware(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def _timestamp(value):
    return _aware(value).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _not_found():
    raise APIError(404, "not_found", "The requested resource was not found.")


def _unauthorized():
    raise APIError(
        401,
        "unauthorized",
        "A valid session is required.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _canonical_path_uuid(value):
    try:
        parsed = UUID(value)
    except (ValueError, AttributeError) as error:
        raise APIError(422, "invalid_request", "The profile ID is invalid.") from error
    if str(parsed) != value:
        raise APIError(422, "invalid_request", "The profile ID is invalid.")
    return parsed


def _validate_payload(payload):
    try:
        return normalize_and_digest(payload)
    except InvalidPayload as error:
        raise APIError(
            422,
            "invalid_payload",
            "The progression payload is invalid.",
        ) from error


def _revision_body(revision, *, include_payload=True):
    result = {
        "revision": revision.revision,
        "base_revision": revision.base_revision,
        "client_save_id": str(revision.client_save_id),
        "device_id": None if revision.device_id is None else str(revision.device_id),
        "payload_sha256": revision.payload_sha256,
        "created_at": _timestamp(revision.created_at),
    }
    if include_payload:
        result["payload"] = revision.payload
    return result


def _profile_body(session, profile, *, created_revision=None, accepted_revision=None):
    revision = session.get(
        ProfileRevision, (profile.id, profile.current_revision)
    )
    if revision is None:
        raise RuntimeError("profile head revision is missing")
    result = {
        "profile_id": str(profile.id),
        "account_id": str(profile.account_id),
        "current_revision": profile.current_revision,
        "head": _revision_body(revision),
    }
    if created_revision is not None:
        result["created_revision"] = created_revision
    if accepted_revision is not None:
        result["accepted_revision"] = accepted_revision
    return result


def _profile_claim_retry(session, profile, account_id, client_save_id, digest):
    if profile.account_id != account_id:
        _not_found()
    original = session.scalar(
        select(ProfileRevision).where(
            ProfileRevision.profile_id == profile.id,
            ProfileRevision.client_save_id == client_save_id,
        )
    )
    if (
        original is None
        or original.revision != 1
        or original.base_revision is not None
        or original.payload_sha256 != digest
    ):
        raise APIError(
            409,
            "profile_conflict",
            "The profile already exists with different initial data.",
        )
    return _profile_body(session, profile, created_revision=1)


def create_app(*, session_factory, settings=None):
    app = FastAPI(title="Dungeon Drifters Profile API", version="1.0.0")
    app.state.session_factory = session_factory
    app.state.settings = settings or Settings.from_environment()
    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(RequestValidationError, request_validation_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(Exception, internal_error_handler)

    def get_db(request: Request):
        session = request.app.state.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def authenticated_session(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
        session: Session = Depends(get_db, scope="function"),
    ):
        if credentials is None or credentials.scheme.lower() != "bearer":
            _unauthorized()
        token_hash = _token_hash(credentials.credentials)
        record = session.scalar(
            select(AccountSession).where(
                AccountSession.access_token_hash == token_hash
            )
        )
        now = utc_now()
        if (
            record is None
            or record.revoked_at is not None
            or _aware(record.access_expires_at) <= now
        ):
            _unauthorized()
        account = session.get(Account, record.account_id)
        if account is None or account.status != "active":
            _unauthorized()
        return account, record

    @app.get("/v1/health", response_model=HealthResponse)
    def health(session: Session = Depends(get_db, scope="function")):
        try:
            session.execute(text("SELECT 1"))
        except SQLAlchemyError as error:
            raise APIError(
                503,
                "service_unavailable",
                "The profile service is temporarily unavailable.",
            ) from error
        return {"status": "ok", "api_version": "v1"}

    @app.post(
        "/v1/accounts/anonymous",
        status_code=201,
        response_model=AnonymousAccountResponse,
    )
    def create_anonymous_account(
        request: AnonymousAccountRequest,
        session: Session = Depends(get_db, scope="function"),
    ):
        now = utc_now()
        settings = app.state.settings
        access_token = _new_token()
        refresh_token = _new_token()
        account = Account(id=uuid4(), status="active", created_at=now, updated_at=now)
        account_session = AccountSession(
            id=uuid4(),
            account_id=account.id,
            access_token_hash=_token_hash(access_token),
            refresh_token_hash=_token_hash(refresh_token),
            device_id=request.device_id,
            access_expires_at=now + settings.access_token_ttl,
            refresh_expires_at=now + settings.refresh_token_ttl,
            created_at=now,
        )
        session.add_all((account, account_session))
        session.flush()
        return {
            "account_id": str(account.id),
            "access_token": access_token,
            "access_expires_at": _timestamp(account_session.access_expires_at),
            "refresh_token": refresh_token,
            "refresh_expires_at": _timestamp(account_session.refresh_expires_at),
        }

    @app.post("/v1/sessions/refresh", response_model=RefreshResponse)
    def refresh_session(
        request: RefreshRequest,
        session: Session = Depends(get_db, scope="function"),
    ):
        record = session.scalar(
            select(AccountSession)
            .where(AccountSession.refresh_token_hash == _token_hash(request.refresh_token))
            .with_for_update()
        )
        now = utc_now()
        account = None if record is None else session.get(Account, record.account_id)
        if (
            record is None
            or record.revoked_at is not None
            or _aware(record.refresh_expires_at) <= now
            or account is None
            or account.status != "active"
        ):
            _unauthorized()
        access_token = _new_token()
        record.access_token_hash = _token_hash(access_token)
        record.access_expires_at = now + app.state.settings.access_token_ttl
        session.flush()
        return {
            "access_token": access_token,
            "access_expires_at": _timestamp(record.access_expires_at),
        }

    @app.delete("/v1/sessions/current", status_code=204, response_class=Response)
    def revoke_current_session(
        principal=Depends(authenticated_session),
    ):
        _, record = principal
        record.revoked_at = utc_now()
        return None

    @app.get("/v1/profiles", response_model=ProfileListResponse)
    def list_profiles(
        principal=Depends(authenticated_session),
        session: Session = Depends(get_db, scope="function"),
    ):
        account, _ = principal
        profiles = session.scalars(
            select(Profile)
            .where(Profile.account_id == account.id, Profile.status == "active")
            .order_by(Profile.created_at, Profile.id)
        ).all()
        return {
            "profiles": [
                {
                    "profile_id": str(profile.id),
                    "current_revision": profile.current_revision,
                    "created_at": _timestamp(profile.created_at),
                    "updated_at": _timestamp(profile.updated_at),
                }
                for profile in profiles
            ]
        }

    @app.post(
        "/v1/profiles",
        status_code=201,
        response_model=ProfileResponse,
        response_model_exclude_unset=True,
    )
    def create_or_claim_profile(
        request: CreateProfileRequest,
        response: Response,
        principal=Depends(authenticated_session),
        session: Session = Depends(get_db, scope="function"),
    ):
        account, _ = principal
        payload, digest = _validate_payload(request.payload)
        profile = session.scalar(
            select(Profile).where(Profile.id == request.profile_id).with_for_update()
        )
        if profile is not None:
            response.status_code = 200
            return _profile_claim_retry(
                session,
                profile,
                account.id,
                request.client_save_id,
                digest,
            )

        now = utc_now()
        profile = Profile(
            id=request.profile_id,
            account_id=account.id,
            current_revision=1,
            status="active",
            created_at=now,
            updated_at=now,
        )
        revision = ProfileRevision(
            profile_id=profile.id,
            revision=1,
            base_revision=None,
            client_save_id=request.client_save_id,
            device_id=request.device_id,
            payload=payload,
            payload_sha256=digest,
            created_at=now,
        )
        try:
            with session.begin_nested():
                session.add_all((profile, revision))
                session.flush()
        except IntegrityError:
            existing = session.scalar(
                select(Profile).where(Profile.id == request.profile_id)
            )
            if existing is None:
                raise
            response.status_code = 200
            return _profile_claim_retry(
                session,
                existing,
                account.id,
                request.client_save_id,
                digest,
            )
        return _profile_body(session, profile, created_revision=1)

    @app.get(
        "/v1/profiles/{profile_id}",
        response_model=ProfileResponse,
        response_model_exclude_unset=True,
    )
    def read_profile(
        profile_id: str,
        principal=Depends(authenticated_session),
        session: Session = Depends(get_db, scope="function"),
    ):
        account, _ = principal
        profile_uuid = _canonical_path_uuid(profile_id)
        profile = session.scalar(
            select(Profile).where(
                Profile.id == profile_uuid,
                Profile.account_id == account.id,
                Profile.status == "active",
            )
        )
        if profile is None:
            _not_found()
        return _profile_body(session, profile)

    @app.put(
        "/v1/profiles/{profile_id}/progression",
        response_model=ProfileResponse,
        response_model_exclude_unset=True,
    )
    def submit_progression(
        profile_id: str,
        request: ProgressionRequest,
        principal=Depends(authenticated_session),
        session: Session = Depends(get_db, scope="function"),
    ):
        account, _ = principal
        profile_uuid = _canonical_path_uuid(profile_id)
        profile = session.scalar(
            select(Profile)
            .where(
                Profile.id == profile_uuid,
                Profile.account_id == account.id,
                Profile.status == "active",
            )
            .with_for_update()
        )
        if profile is None:
            _not_found()
        payload, digest = _validate_payload(request.payload)
        previous = session.scalar(
            select(ProfileRevision).where(
                ProfileRevision.profile_id == profile.id,
                ProfileRevision.client_save_id == request.client_save_id,
            )
        )
        if previous is not None:
            if previous.payload_sha256 != digest:
                raise APIError(
                    409,
                    "idempotency_key_reuse",
                    "The save ID was already used for different progression data.",
                )
            return _profile_body(
                session,
                profile,
                accepted_revision=previous.revision,
            )
        if request.base_revision != profile.current_revision:
            head = session.get(
                ProfileRevision, (profile.id, profile.current_revision)
            )
            raise APIError(
                409,
                "stale_revision",
                "The profile changed on another device.",
                extra={
                    "current_head": {
                        "revision": head.revision,
                        "client_save_id": str(head.client_save_id),
                        "payload_sha256": head.payload_sha256,
                        "created_at": _timestamp(head.created_at),
                    }
                },
            )
        new_revision = profile.current_revision + 1
        now = utc_now()
        session.add(
            ProfileRevision(
                profile_id=profile.id,
                revision=new_revision,
                base_revision=profile.current_revision,
                client_save_id=request.client_save_id,
                device_id=request.device_id,
                payload=payload,
                payload_sha256=digest,
                created_at=now,
            )
        )
        profile.current_revision = new_revision
        profile.updated_at = now
        session.flush()
        return _profile_body(
            session,
            profile,
            accepted_revision=new_revision,
        )

    @app.get("/v1/entitlements", response_model=EntitlementListResponse)
    def list_entitlements(
        principal=Depends(authenticated_session),
        session: Session = Depends(get_db, scope="function"),
    ):
        account, _ = principal
        entitlements = session.scalars(
            select(Entitlement)
            .where(Entitlement.account_id == account.id)
            .order_by(Entitlement.granted_at, Entitlement.id)
        ).all()
        return {
            "entitlements": [
                {
                    "id": str(item.id),
                    "product_key": item.product_key,
                    "source_provider": item.source_provider,
                    "status": item.status,
                    "granted_at": _timestamp(item.granted_at),
                    "expires_at": None
                    if item.expires_at is None
                    else _timestamp(item.expires_at),
                    "revoked_at": None
                    if item.revoked_at is None
                    else _timestamp(item.revoked_at),
                    "metadata": item.metadata_json,
                }
                for item in entitlements
            ]
        }

    return app

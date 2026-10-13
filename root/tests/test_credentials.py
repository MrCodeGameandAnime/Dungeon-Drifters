from datetime import datetime, timezone
from uuid import UUID

from app.content.catalog import get_drifter_spec_by_choice
from app.game.game_state import GameState
from app.persistence.account import AccountCredentials
from app.persistence.coordinator import SaveCoordinator
from app.persistence.credentials import is_credential_store
from app.persistence.envelope import SyncState, serialize_profile_envelope
from app.persistence.local_store import LocalProfileStore
from app.persistence.ports import SaveLoadStatus
from app.persistence.save_document import build_save_document
from app.player.player_state import PlayerState
from tests.credential_test_support import MemoryCredentialStore


def _credentials():
    return AccountCredentials.from_anonymous_response(
        {
            "account_id": "00000000-0000-4000-8000-000000000004",
            "access_token": "access-secret-for-test",
            "access_expires_at": "2026-10-13T12:15:00.000000Z",
            "refresh_token": "refresh-secret-for-test",
            "refresh_expires_at": "2026-11-12T12:00:00.000000Z",
        }
    )


def test_credentials_parse_refresh_without_rotation_and_redact_secrets():
    credentials = _credentials()
    refreshed = credentials.with_refreshed_access_response(
        {
            "access_token": "new-access-secret",
            "access_expires_at": "2026-10-13T12:30:00.000000Z",
        }
    )

    assert credentials.account_id == UUID("00000000-0000-4000-8000-000000000004")
    assert refreshed.access_token == "new-access-secret"
    assert refreshed.refresh_token == credentials.refresh_token
    assert refreshed.refresh_expires_at == credentials.refresh_expires_at
    assert credentials.access_token not in repr(credentials)
    assert credentials.refresh_token not in repr(credentials)


def test_memory_credential_store_is_separate_from_offline_profile_save(tmp_path):
    profile_id = UUID("00000000-0000-4000-8000-000000000001")
    store = LocalProfileStore(tmp_path / "profiles")
    coordinator = SaveCoordinator(store, profile_id)
    character = get_drifter_spec_by_choice("1").create_character()
    game_state = GameState(PlayerState(character))
    assert coordinator.save(game_state).status is SaveLoadStatus.SAVED

    credential_store = MemoryCredentialStore()
    assert is_credential_store(credential_store)
    credentials = _credentials()
    credential_store.save(credentials)
    envelope = store.load(profile_id).envelope
    encoded = serialize_profile_envelope(envelope)
    assert credentials.access_token.encode() not in encoded
    assert credentials.refresh_token.encode() not in encoded

    credential_store.clear()

    assert credential_store.load() is None
    loaded = coordinator.load()
    assert loaded.status is SaveLoadStatus.LOADED
    assert build_save_document(loaded.game_state) == build_save_document(game_state)


def test_credential_response_requires_exact_fields_and_canonical_account_id():
    document = {
        "account_id": "00000000-0000-4000-8000-000000000004",
        "access_token": "access",
        "access_expires_at": "2026-10-13T12:15:00.000000Z",
        "refresh_token": "refresh",
        "refresh_expires_at": "2026-11-12T12:00:00.000000Z",
    }
    malformed = dict(document, account_id="00000000000040008000000000000004")
    extra = dict(document, provider_subject="not-client-owned")

    try:
        AccountCredentials.from_anonymous_response(malformed)
    except ValueError:
        pass
    else:
        raise AssertionError("non-canonical account ID was accepted")

    try:
        AccountCredentials.from_anonymous_response(extra)
    except ValueError:
        pass
    else:
        raise AssertionError("unknown credential response field was accepted")


def test_credential_timestamps_are_utc_z_values():
    credentials = _credentials()

    assert credentials.access_expires_at.tzinfo is timezone.utc
    assert credentials.access_expires_at == datetime(
        2026, 10, 13, 12, 15, tzinfo=timezone.utc
    )

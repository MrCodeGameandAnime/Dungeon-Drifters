from dataclasses import replace
from datetime import datetime, timezone
from uuid import UUID

import pytest

from app.content.catalog import get_drifter_spec_by_choice
from app.game.game_state import GameState
from app.persistence.envelope import (
    SyncState,
    build_conflict_snapshot,
    build_profile_envelope,
)
from app.persistence.local_store import LocalProfileStore, ProfileStoreError
from app.persistence.ports import ConflictStoreStatus, ProfileStoreStatus
from app.persistence.save_document import build_save_document
from app.player.player_state import PlayerState


PROFILE_ID = UUID("00000000-0000-4000-8000-000000000001")
SAVE_ID = UUID("00000000-0000-4000-8000-000000000002")
ACCOUNT_ID = UUID("00000000-0000-4000-8000-000000000004")
SAVED_AT = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)


def _payload(marker=None):
    character = get_drifter_spec_by_choice("1").create_character()
    game = GameState(PlayerState(character))
    if marker is not None:
        game.set_metadata("branch", marker)
    return build_save_document(game)


def _envelope(*, sequence=1, payload=None, **changes):
    options = {
        "profile_id": PROFILE_ID,
        "client_save_id": SAVE_ID,
        "local_sequence": sequence,
        "saved_at": SAVED_AT,
    }
    options.update(changes)
    return build_profile_envelope(_payload() if payload is None else payload, **options)


def test_store_uses_injected_root_and_distinguishes_missing_valid_and_invalid(tmp_path):
    store = LocalProfileStore(tmp_path / "profiles-home")

    missing = store.inspect(PROFILE_ID)
    assert missing.status is ProfileStoreStatus.MISSING
    assert not (tmp_path / "profiles-home").exists()

    envelope = _envelope()
    store.save(envelope)
    path = tmp_path / "profiles-home" / "profiles" / f"{PROFILE_ID}.json"
    assert path.is_file()
    assert not path.read_bytes().endswith(b"\n")
    assert store.inspect(PROFILE_ID).status is ProfileStoreStatus.VALID
    loaded = store.load(PROFILE_ID)
    assert loaded.status is ProfileStoreStatus.VALID
    assert loaded.envelope == envelope
    assert store.list_profiles() == (PROFILE_ID,)

    path.write_bytes(b"not-json")
    invalid = store.load(PROFILE_ID)
    assert invalid.status is ProfileStoreStatus.INVALID
    assert invalid.envelope is None
    assert path.read_bytes() == b"not-json"


def test_store_never_moves_sequence_backwards_or_changes_payload_at_same_sequence(tmp_path):
    store = LocalProfileStore(tmp_path)
    initial = _envelope(sequence=2)
    store.save(initial)
    path = tmp_path / "profiles" / f"{PROFILE_ID}.json"
    before = path.read_bytes()

    with pytest.raises(ProfileStoreError):
        store.save(_envelope(sequence=1))
    with pytest.raises(ProfileStoreError):
        store.save(_envelope(sequence=2, payload=_payload("changed")))
    with pytest.raises(ProfileStoreError):
        store.save(_envelope(sequence=3, payload=_payload("next")))

    assert path.read_bytes() == before


def test_store_allows_metadata_only_sync_transition_at_same_local_sequence(tmp_path):
    store = LocalProfileStore(tmp_path)
    local = _envelope()
    store.save(local)
    pending = _envelope(
        account_id=ACCOUNT_ID,
        sync_state=SyncState.PENDING,
    )

    store.save(pending)

    assert store.load(PROFILE_ID).envelope == pending


def test_failed_atomic_replace_preserves_previous_profile_and_cleans_temp_files(
    tmp_path, monkeypatch
):
    store = LocalProfileStore(tmp_path)
    initial = _envelope()
    store.save(initial)
    path = tmp_path / "profiles" / f"{PROFILE_ID}.json"
    before = path.read_bytes()

    def fail_replace(source, destination):
        raise OSError("simulated replacement failure")

    monkeypatch.setattr("app.persistence.local_store.os.replace", fail_replace)
    with pytest.raises(ProfileStoreError):
        store.save(_envelope(sequence=2, payload=_payload("next")))

    assert path.read_bytes() == before
    assert list(path.parent.glob("*.tmp")) == []


def test_invalid_envelope_cannot_replace_valid_profile(tmp_path):
    store = LocalProfileStore(tmp_path)
    initial = _envelope()
    store.save(initial)
    path = tmp_path / "profiles" / f"{PROFILE_ID}.json"
    before = path.read_bytes()
    invalid = replace(initial, payload_sha256="0" * 64)

    with pytest.raises(ProfileStoreError):
        store.save(invalid)

    assert path.read_bytes() == before


def test_conflict_snapshot_is_separate_validated_and_immutable_until_cleared(tmp_path):
    store = LocalProfileStore(tmp_path)
    conflict = build_conflict_snapshot(
        profile_id=PROFILE_ID,
        local_client_save_id=SAVE_ID,
        local_payload=_payload("local"),
        base_remote_revision=1,
        remote_current_revision=2,
        remote_payload=_payload("remote"),
        detected_at=SAVED_AT,
    )

    store.save_conflict(conflict)

    path = tmp_path / "conflicts" / f"{PROFILE_ID}.json"
    assert path.is_file()
    assert store.load_conflict(PROFILE_ID).status is ConflictStoreStatus.VALID
    assert store.load_conflict(PROFILE_ID).snapshot == conflict
    store.save_conflict(conflict)

    changed = build_conflict_snapshot(
        profile_id=PROFILE_ID,
        local_client_save_id=SAVE_ID,
        local_payload=_payload("new-local"),
        base_remote_revision=1,
        remote_current_revision=3,
        remote_payload=_payload("new-remote"),
        detected_at=SAVED_AT,
    )
    with pytest.raises(ProfileStoreError):
        store.save_conflict(changed)

    store.clear_conflict(PROFILE_ID)
    assert store.load_conflict(PROFILE_ID).status is ConflictStoreStatus.MISSING


def test_recovery_archives_preserve_profile_and_conflict_as_immutable_records(tmp_path):
    store = LocalProfileStore(tmp_path)
    local = _envelope(
        account_id=ACCOUNT_ID,
        remote_revision=1,
        sync_state=SyncState.CONFLICT,
        payload=_payload("local"),
    )
    conflict = build_conflict_snapshot(
        profile_id=PROFILE_ID,
        local_client_save_id=SAVE_ID,
        local_payload=local.payload,
        base_remote_revision=1,
        remote_current_revision=2,
        remote_payload=_payload("remote"),
        detected_at=SAVED_AT,
    )

    store.archive_recovery(local, conflict)
    store.archive_recovery(local, conflict)

    archived_profile = store.load_recovery_profile(PROFILE_ID, SAVE_ID)
    archived_conflict = store.load_recovery_conflict(PROFILE_ID, SAVE_ID, 2)
    assert archived_profile.status is ProfileStoreStatus.VALID
    assert archived_profile.envelope == local
    assert archived_conflict.status is ConflictStoreStatus.VALID
    assert archived_conflict.snapshot == conflict

    changed = _envelope(
        account_id=ACCOUNT_ID,
        remote_revision=1,
        sync_state=SyncState.CONFLICT,
        payload=_payload("changed"),
    )
    with pytest.raises(ProfileStoreError):
        store.archive_recovery(changed, conflict)

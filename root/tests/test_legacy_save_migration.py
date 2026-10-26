import json
from datetime import datetime, timezone
from uuid import UUID

import pytest

from app.content.catalog import get_drifter_spec_by_choice
from app.game.game_state import GameState
from app.persistence.envelope import SyncState
from app.persistence.local_store import LocalProfileStore
from app.persistence.migration import (
    LegacyMigrationStatus,
    migrate_legacy_save,
)
from app.persistence.ports import ProfileStoreStatus
from app.persistence.save_document import build_save_document, reconstruct_game_state
from app.player.player_state import PlayerState


PROFILE_ID = UUID("00000000-0000-4000-8000-000000000001")
SAVE_ID = UUID("00000000-0000-4000-8000-000000000002")
SAVED_AT = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)


def _game_state():
    character = get_drifter_spec_by_choice("1").create_character()
    game = GameState(PlayerState(character))
    game.set_metadata("campaign", "legacy")
    return game


def _migrate(path, store):
    return migrate_legacy_save(
        path,
        store,
        profile_id_factory=lambda: PROFILE_ID,
        client_save_id_factory=lambda: SAVE_ID,
        now_factory=lambda: SAVED_AT,
    )


def test_schema8_legacy_save_is_wrapped_without_modifying_original(tmp_path):
    legacy_path = tmp_path / "legacy" / "dungeon_drifters.json"
    legacy_path.parent.mkdir()
    original_payload = build_save_document(_game_state())
    original_payload["schema_version"] = 8
    original_payload.pop("party")
    original_payload["player"].pop("signature_weapon")
    original_payload["overworld"].pop("active_route_id")
    original_bytes = json.dumps(original_payload, ensure_ascii=False).encode("utf-8")
    legacy_path.write_bytes(original_bytes)
    store = LocalProfileStore(tmp_path / "data")

    result = _migrate(legacy_path, store)

    assert result.status is LegacyMigrationStatus.MIGRATED
    assert result.profile_id == PROFILE_ID
    assert result.migrated_from_schema_7 is False
    assert legacy_path.read_bytes() == original_bytes
    loaded = store.load(PROFILE_ID)
    assert loaded.status is ProfileStoreStatus.VALID
    assert loaded.envelope.sync_state is SyncState.LOCAL_ONLY
    assert loaded.envelope.payload["schema_version"] == 11
    assert loaded.envelope.payload == build_save_document(
        reconstruct_game_state(original_payload)
    )


def test_schema7_legacy_save_migrates_in_memory_before_enveloping(tmp_path):
    legacy_path = tmp_path / "dungeon_drifters.json"
    original_payload = _game_state().snapshot()
    original_payload["schema_version"] = 7
    original_payload.pop("party", None)
    original_payload["player"].pop("signature_weapon")
    original_bytes = json.dumps(original_payload, ensure_ascii=False).encode("utf-8")
    legacy_path.write_bytes(original_bytes)
    store = LocalProfileStore(tmp_path / "data")

    result = _migrate(legacy_path, store)

    assert result.status is LegacyMigrationStatus.MIGRATED
    assert result.migrated_from_schema_7 is True
    assert legacy_path.read_bytes() == original_bytes
    loaded = store.load(PROFILE_ID)
    assert loaded.envelope.payload["schema_version"] == 11
    assert build_save_document(reconstruct_game_state(loaded.envelope.payload)) == (
        build_save_document(reconstruct_game_state(original_payload))
    )


@pytest.mark.parametrize("raw", (b"not-json", b'{"schema_version":9}'))
def test_invalid_legacy_save_is_reported_and_never_modified(tmp_path, raw):
    legacy_path = tmp_path / "dungeon_drifters.json"
    legacy_path.write_bytes(raw)
    store = LocalProfileStore(tmp_path / "data")

    result = _migrate(legacy_path, store)

    assert result.status is LegacyMigrationStatus.INVALID
    assert legacy_path.read_bytes() == raw
    assert store.list_profiles() == ()


def test_repeated_legacy_migration_does_not_create_a_new_profile_id(tmp_path):
    legacy_path = tmp_path / "dungeon_drifters.json"
    legacy_path.write_text(
        json.dumps(build_save_document(_game_state())),
        encoding="utf-8",
    )
    store = LocalProfileStore(tmp_path / "data")

    first = _migrate(legacy_path, store)
    second = _migrate(legacy_path, store)

    assert first.status is LegacyMigrationStatus.MIGRATED
    assert second.status is LegacyMigrationStatus.ALREADY_PRESENT
    assert second.profile_id == first.profile_id == PROFILE_ID
    assert store.list_profiles() == (PROFILE_ID,)


def test_missing_legacy_file_does_not_create_storage_root(tmp_path):
    store = LocalProfileStore(tmp_path / "data")

    result = _migrate(tmp_path / "missing.json", store)

    assert result.status is LegacyMigrationStatus.MISSING
    assert not store.root.exists()

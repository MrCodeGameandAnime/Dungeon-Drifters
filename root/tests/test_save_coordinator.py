import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest

from app.content.catalog import get_drifter_spec_by_choice
from app.game.game_state import GameState
from app.persistence.bootstrap import (
    build_default_save_port,
    default_profile_root,
)
from app.persistence.coordinator import SaveCoordinator
from app.persistence.envelope import SyncState
from app.persistence.local_store import LocalProfileStore
from app.persistence.ports import ProfileStoreError, SaveLoadStatus
from app.persistence.save_document import build_save_document
from app.player.player_state import PlayerState


PROFILE_ID = UUID("00000000-0000-4000-8000-000000000001")
SAVED_AT = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)


def _game_state(gold=0):
    character = get_drifter_spec_by_choice("1").create_character()
    return GameState(PlayerState(character, gold=gold))


def _coordinator(root):
    return SaveCoordinator(
        LocalProfileStore(root),
        PROFILE_ID,
        now_factory=lambda: SAVED_AT,
    )


def test_local_save_creates_profile_envelope_without_mutating_game_state(tmp_path):
    state = _game_state(gold=12)
    before = state.snapshot()
    store = LocalProfileStore(tmp_path / "profiles-home")
    coordinator = SaveCoordinator(
        store,
        PROFILE_ID,
        client_save_id_factory=lambda: UUID(
            "00000000-0000-4000-8000-000000000002"
        ),
        now_factory=lambda: SAVED_AT,
    )

    result = coordinator.save(state)

    assert result.status is SaveLoadStatus.SAVED
    assert result.error is None
    assert state.snapshot() == before
    envelope = store.load(PROFILE_ID).envelope
    assert envelope.profile_id == PROFILE_ID
    assert envelope.local_sequence == 1
    assert envelope.account_id is None
    assert envelope.remote_revision is None
    assert envelope.sync_state is SyncState.LOCAL_ONLY
    assert envelope.payload == build_save_document(state)


def test_each_local_save_advances_sequence_and_uses_a_new_save_id(tmp_path):
    store = LocalProfileStore(tmp_path / "profiles-home")
    coordinator = _coordinator(store.root)
    first = coordinator.save(_game_state(gold=1))
    first_save_id = store.load(PROFILE_ID).envelope.client_save_id
    second = coordinator.save(_game_state(gold=2))

    assert first.status is SaveLoadStatus.SAVED
    assert second.status is SaveLoadStatus.SAVED
    envelope = store.load(PROFILE_ID).envelope
    assert envelope.local_sequence == 2
    assert envelope.client_save_id != first_save_id
    assert envelope.payload["player"]["gold"] == 2


def test_restart_load_returns_a_fresh_game_state_from_the_same_profile(tmp_path):
    store = LocalProfileStore(tmp_path / "profiles-home")
    first_process = _coordinator(store.root)
    original = _game_state(gold=12)
    assert first_process.save(original).status is SaveLoadStatus.SAVED

    restarted = build_default_save_port(
        storage_root=store.root,
        legacy_path=tmp_path / "missing-legacy.json",
        profile_id_factory=lambda: UUID(
            "00000000-0000-4000-8000-000000000099"
        ),
        client_save_id_factory=lambda: UUID(
            "00000000-0000-4000-8000-000000000098"
        ),
        now_factory=lambda: SAVED_AT,
    )
    loaded = restarted.load()

    assert restarted.profile_id == PROFILE_ID
    assert loaded.status is SaveLoadStatus.LOADED
    assert loaded.game_state is not original
    assert loaded.game_state.snapshot() == original.snapshot()


def test_invalid_profile_is_reported_and_not_overwritten(tmp_path):
    store = LocalProfileStore(tmp_path / "profiles-home")
    coordinator = _coordinator(store.root)
    assert coordinator.save(_game_state()).status is SaveLoadStatus.SAVED
    path = store.root / "profiles" / f"{PROFILE_ID}.json"
    path.write_text("not-json", encoding="utf-8")
    before = path.read_bytes()

    inspection = coordinator.inspect()
    save = coordinator.save(_game_state(gold=99))
    load = coordinator.load()

    assert inspection.status is SaveLoadStatus.INVALID
    assert save.status is SaveLoadStatus.INVALID
    assert load.status is SaveLoadStatus.INVALID
    assert path.read_bytes() == before


@pytest.mark.parametrize("failure", (OSError("read failed"), ProfileStoreError("read failed")))
def test_store_errors_during_inspect_load_and_save_return_invalid(tmp_path, failure):
    class FailingStore:
        def inspect(self, profile_id):
            raise failure

        def load(self, profile_id):
            raise failure

        def save(self, envelope):
            raise failure

    coordinator = SaveCoordinator(FailingStore(), PROFILE_ID)

    assert coordinator.inspect().status is SaveLoadStatus.INVALID
    assert coordinator.load().status is SaveLoadStatus.INVALID
    assert coordinator.save(_game_state()).status is SaveLoadStatus.INVALID


@pytest.mark.parametrize(
    ("system", "environment", "home", "expected"),
    (
        (
            "Windows",
            {"LOCALAPPDATA": "C:/Users/player/AppData/Local"},
            "C:/Users/player",
            "C:/Users/player/AppData/Local/Dungeon Drifters",
        ),
        (
            "Linux",
            {"XDG_DATA_HOME": "/home/player/.local/share"},
            "/home/player",
            "/home/player/.local/share/dungeon-drifters",
        ),
        (
            "Linux",
            {},
            "/home/player",
            "/home/player/.local/share/dungeon-drifters",
        ),
    ),
)
def test_default_storage_root_is_host_user_data_not_source_tree(
    system, environment, home, expected
):
    assert default_profile_root(
        system=system,
        environ=environment,
        home=home,
    ) == Path(expected)


def test_bootstrap_migrates_legacy_save_before_selecting_default_profile(tmp_path):
    legacy_path = tmp_path / "legacy.json"
    legacy_path.write_text(
        json.dumps(build_save_document(_game_state(gold=33))),
        encoding="utf-8",
    )

    coordinator = build_default_save_port(
        storage_root=tmp_path / "app-data",
        legacy_path=legacy_path,
        profile_id_factory=lambda: PROFILE_ID,
        client_save_id_factory=lambda: UUID(
            "00000000-0000-4000-8000-000000000002"
        ),
        now_factory=lambda: SAVED_AT,
    )

    loaded = coordinator.load()

    assert coordinator.profile_id == PROFILE_ID
    assert loaded.status is SaveLoadStatus.LOADED
    assert loaded.game_state.player_state.gold == 33
    assert legacy_path.is_file()

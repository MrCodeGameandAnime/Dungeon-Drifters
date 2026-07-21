import json

import pytest

from app.game.game_state import GameState
from app.game.save_repository import (
    SAVE_DIRECTORY,
    SAVE_PATH,
    SaveLoadStatus,
    SaveRepository,
    SaveRepositoryError,
)
from app.game.save_state import SaveStateValidationError
from app.player.character import Brawler
from app.player.player_state import PlayerState
from app.world.character_profiles.roster import get_profile_by_choice


def _game_state():
    player = PlayerState(
        get_profile_by_choice("1").create_character(),
        gold=12,
    )
    game = GameState(player)
    game.set_metadata("run_id", "repository-test")
    player.health.take_damage(9)
    player.mana_resource.spend(4)
    player.super_resource.gain(30)
    player.inventory.add_item("tonic")
    return game


def test_save_path_is_the_approved_src_saves_location():
    assert SAVE_DIRECTORY == SAVE_PATH.parent
    assert SAVE_DIRECTORY.name == "saves"
    assert SAVE_PATH.name == "dungeon_drifters.json"
    assert SAVE_PATH.parent.parent.name == "src"


def test_save_creates_directory_and_writes_schema8_without_combat(tmp_path):
    repository = SaveRepository(tmp_path / "saves" / "dungeon_drifters.json")

    saved_path = repository.save(_game_state())

    assert saved_path == repository.path
    assert saved_path.is_file()
    document = json.loads(saved_path.read_text(encoding="utf-8"))
    assert document["schema_version"] == 8
    assert "combat" not in document["player"]
    assert list(saved_path.parent.glob("*.tmp")) == []


def test_missing_save_is_normal_new_game_signal(tmp_path):
    path = tmp_path / "saves" / "dungeon_drifters.json"

    result = SaveRepository(path).load()

    assert result.status is SaveLoadStatus.MISSING
    assert result.game_state is None
    assert result.error is None
    assert not path.parent.exists()


def test_valid_save_loads_as_fresh_game_state(tmp_path):
    repository = SaveRepository(tmp_path / "dungeon_drifters.json")
    game = _game_state()
    repository.save(game)

    result = repository.load()

    assert result.status is SaveLoadStatus.LOADED
    assert result.game_state is not game
    assert result.game_state.player_state is not game.player_state
    assert result.game_state.snapshot()["player"]["gold"] == 12
    assert result.game_state.snapshot()["metadata"] == {
        "run_id": "repository-test"
    }
    assert result.migrated_from_schema_7 is False


def test_schema7_load_migrates_in_memory_without_rewriting_file(tmp_path):
    path = tmp_path / "dungeon_drifters.json"
    schema7 = _game_state().snapshot()
    original_bytes = json.dumps(schema7, ensure_ascii=False).encode("utf-8")
    path.write_bytes(original_bytes)

    result = SaveRepository(path).load()

    assert result.status is SaveLoadStatus.LOADED
    assert result.migrated_from_schema_7 is True
    assert path.read_bytes() == original_bytes


@pytest.mark.parametrize(
    "write_invalid",
    (
        lambda path: path.write_text("not json", encoding="utf-8"),
        lambda path: path.write_text(
            json.dumps({"schema_version": 9}),
            encoding="utf-8",
        ),
        lambda path: path.write_text(
            json.dumps({"schema_version": 8, "player": {}}),
            encoding="utf-8",
        ),
    ),
)
def test_invalid_save_is_reported_without_mutating_the_file(tmp_path, write_invalid):
    path = tmp_path / "dungeon_drifters.json"
    write_invalid(path)
    before = path.read_bytes()

    result = SaveRepository(path).load()

    assert result.status is SaveLoadStatus.INVALID
    assert result.game_state is None
    assert result.error == "The save file is invalid and was not loaded."
    assert path.read_bytes() == before


def test_failed_atomic_replacement_preserves_previous_valid_save(tmp_path, monkeypatch):
    path = tmp_path / "dungeon_drifters.json"
    repository = SaveRepository(path)
    repository.save(_game_state())
    before = path.read_bytes()

    def fail_replace(source, target):
        raise OSError("simulated replacement failure")

    monkeypatch.setattr("app.game.save_repository.os.replace", fail_replace)
    with pytest.raises(SaveRepositoryError):
        repository.save(_game_state())

    assert path.read_bytes() == before
    assert list(path.parent.glob("*.tmp")) == []


def test_save_validation_failure_does_not_replace_existing_save(tmp_path):
    path = tmp_path / "dungeon_drifters.json"
    repository = SaveRepository(path)
    repository.save(_game_state())
    before = path.read_bytes()
    invalid_game = GameState(PlayerState(Brawler()))

    with pytest.raises(SaveStateValidationError):
        repository.save(invalid_game)

    assert path.read_bytes() == before

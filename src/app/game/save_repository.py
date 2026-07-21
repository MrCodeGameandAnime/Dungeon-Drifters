"""Atomic disk access for the validated M10 save document."""

import json
import os
import tempfile
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from app.game.game_state import GameState
from app.game.save_state import (
    build_save_document,
    reconstruct_game_state,
)


SAVE_DIRECTORY = Path(__file__).resolve().parents[2] / "saves"
SAVE_PATH = SAVE_DIRECTORY / "dungeon_drifters.json"


class SaveLoadStatus(StrEnum):
    MISSING = "missing"
    LOADED = "loaded"
    INVALID = "invalid"


@dataclass(frozen=True)
class SaveLoadResult:
    status: SaveLoadStatus
    game_state: GameState | None = None
    error: str | None = None
    migrated_from_schema_7: bool = False


class SaveRepositoryError(RuntimeError):
    """Raised when an atomic save write cannot complete."""


class SaveRepository:
    def __init__(self, path=SAVE_PATH):
        self._path = Path(path)

    @property
    def path(self):
        return self._path

    def save(self, game_state):
        if not isinstance(game_state, GameState):
            raise TypeError("game_state must be a GameState instance")

        document = build_save_document(game_state)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = None
        try:
            temporary_path = self._write_temporary_document(document)
            with temporary_path.open("r", encoding="utf-8") as stream:
                serialized_document = json.load(stream)
            reconstruct_game_state(serialized_document)
            os.replace(temporary_path, self._path)
            temporary_path = None
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise SaveRepositoryError(
                "save could not be written without replacing the existing file"
            ) from error
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink()
                except FileNotFoundError:
                    pass

        return self._path

    def load(self):
        if not self._path.exists():
            return SaveLoadResult(status=SaveLoadStatus.MISSING)

        try:
            with self._path.open("r", encoding="utf-8") as stream:
                document = json.load(stream)
            schema_version = document.get("schema_version")
            game_state = reconstruct_game_state(document)
        except (OSError, TypeError, ValueError, json.JSONDecodeError, AttributeError) as error:
            return SaveLoadResult(
                status=SaveLoadStatus.INVALID,
                error="The save file is invalid and was not loaded.",
            )

        return SaveLoadResult(
            status=SaveLoadStatus.LOADED,
            game_state=game_state,
            migrated_from_schema_7=schema_version == 7,
        )

    def _write_temporary_document(self, document):
        temporary = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=self._path.parent,
            prefix=f".{self._path.name}.",
            suffix=".tmp",
            delete=False,
        )
        temporary_path = Path(temporary.name)
        try:
            with temporary:
                json.dump(
                    document,
                    temporary,
                    ensure_ascii=False,
                    allow_nan=False,
                    separators=(",", ":"),
                )
                temporary.flush()
                os.fsync(temporary.fileno())
        except Exception:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass
            raise
        return temporary_path


__all__ = [
    "DISK_SCHEMA_VERSION",
    "SAVE_DIRECTORY",
    "SAVE_PATH",
    "SaveLoadResult",
    "SaveLoadStatus",
    "SaveRepository",
    "SaveRepositoryError",
]

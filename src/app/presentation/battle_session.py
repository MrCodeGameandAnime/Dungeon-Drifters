"""Encounter-local ownership of bounded semantic battle history."""

from app.presentation.battle_models import BattleLogEntry


DEFAULT_MAX_LOG_ENTRIES = 20


class BattlePresentationSession:
    def __init__(self, max_entries=DEFAULT_MAX_LOG_ENTRIES):
        if isinstance(max_entries, bool) or not isinstance(max_entries, int):
            raise TypeError("max_entries must be an integer")
        if max_entries <= 0:
            raise ValueError("max_entries must be positive")

        self._max_entries = max_entries
        self._entries = []

    @property
    def max_entries(self):
        return self._max_entries

    @property
    def entries(self):
        return tuple(self._entries)

    def record(self, entry):
        if not isinstance(entry, BattleLogEntry):
            raise TypeError("entry must be a BattleLogEntry")

        self._entries.append(entry)
        overflow = len(self._entries) - self._max_entries
        if overflow > 0:
            del self._entries[:overflow]

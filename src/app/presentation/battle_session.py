"""Encounter-local ownership of bounded semantic battle history."""

from app.presentation.battle_models import BattleEventType, BattleLogEntry


# Keep enough semantic entries for one complex action and its response.
DEFAULT_MAX_LOG_ENTRIES = 12


class BattlePresentationSession:
    def __init__(self, max_entries=DEFAULT_MAX_LOG_ENTRIES):
        if isinstance(max_entries, bool) or not isinstance(max_entries, int):
            raise TypeError("max_entries must be an integer")
        if max_entries <= 0:
            raise ValueError("max_entries must be positive")

        self._max_entries = max_entries
        self._entries = []
        self._transient_rejection = None

    @property
    def max_entries(self):
        return self._max_entries

    @property
    def entries(self):
        entries = tuple(self._entries)
        if self._transient_rejection is None:
            return entries
        return (*entries, self._transient_rejection)

    def begin_player_turn(self):
        """Replace the displayed history when an accepted player action starts."""
        self._entries.clear()
        self._transient_rejection = None

    def record(self, entry):
        if not isinstance(entry, BattleLogEntry):
            raise TypeError("entry must be a BattleLogEntry")

        self._transient_rejection = None
        self._entries.append(entry)
        overflow = len(self._entries) - self._max_entries
        if overflow > 0:
            del self._entries[:overflow]

    def record_transient_rejection(self, entry):
        """Replace one visible rejection without consuming semantic history."""
        if not isinstance(entry, BattleLogEntry):
            raise TypeError("entry must be a BattleLogEntry")
        if entry.event_type != BattleEventType.INPUT_REJECTED:
            raise ValueError("transient rejection must be an input rejection")
        self._transient_rejection = entry

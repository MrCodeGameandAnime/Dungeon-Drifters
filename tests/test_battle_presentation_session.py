import pytest

from app.presentation.battle_models import BattleEventType, BattleLogEntry
from app.presentation.battle_session import (
    DEFAULT_MAX_LOG_ENTRIES,
    BattlePresentationSession,
)


def _entry(index):
    return BattleLogEntry(
        event_type=BattleEventType.DAMAGE,
        actor_name="Ser Branoc",
        target_name="Goblin",
        action_name=f"move-{index}",
        accepted=True,
        hit=True,
        amount=index,
    )


def test_session_defaults_to_twenty_entries():
    session = BattlePresentationSession()

    assert session.max_entries == DEFAULT_MAX_LOG_ENTRIES == 20
    assert session.entries == ()


def test_session_retention_discards_oldest_entries_and_preserves_order():
    session = BattlePresentationSession(max_entries=3)

    for index in range(5):
        session.record(_entry(index))

    assert tuple(entry.amount for entry in session.entries) == (2, 3, 4)


def test_session_exposes_immutable_entry_snapshots():
    session = BattlePresentationSession()
    session.record(_entry(1))
    snapshot = session.entries

    assert isinstance(snapshot, tuple)
    with pytest.raises(AttributeError):
        snapshot.append(_entry(2))
    session.record(_entry(2))
    assert tuple(entry.amount for entry in snapshot) == (1,)
    assert tuple(entry.amount for entry in session.entries) == (1, 2)


def test_session_accepts_only_semantic_entries():
    session = BattlePresentationSession()

    with pytest.raises(TypeError):
        session.record("Ser Branoc dealt damage.")
    with pytest.raises(TypeError):
        BattlePresentationSession(max_entries=True)
    with pytest.raises(ValueError):
        BattlePresentationSession(max_entries=0)


def test_session_owns_no_combat_state():
    session = BattlePresentationSession()

    assert set(vars(session)) == {"_max_entries", "_entries"}

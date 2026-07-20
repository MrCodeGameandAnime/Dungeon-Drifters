import pytest

from app.presentation.battle_models import (
    BattleEventType,
    BattleLogEntry,
    InputRejectionReason,
)
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


def test_session_defaults_to_twelve_entries_for_complex_actions():
    session = BattlePresentationSession()

    assert session.max_entries == DEFAULT_MAX_LOG_ENTRIES == 12
    assert session.entries == ()


def test_session_retention_discards_oldest_entries_and_preserves_order():
    session = BattlePresentationSession(max_entries=3)

    for index in range(5):
        session.record(_entry(index))

    assert tuple(entry.amount for entry in session.entries) == (2, 3, 4)


def test_session_keeps_complete_current_action_before_eviction():
    session = BattlePresentationSession()
    old_entries = tuple(_entry(index) for index in range(2))
    current_action = tuple(_entry(index + 2) for index in range(10))

    for entry in old_entries + current_action:
        session.record(entry)
    assert tuple(entry.amount for entry in session.entries) == tuple(
        entry.amount for entry in old_entries + current_action
    )

    session.record(_entry(12))

    assert tuple(entry.amount for entry in session.entries) == tuple(
        entry.amount for entry in (old_entries[1],) + current_action + (_entry(12),)
    )


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


def test_begin_player_turn_clears_only_when_orchestrator_starts_accepted_turn():
    session = BattlePresentationSession()
    session.record(_entry(1))
    session.begin_player_turn()

    assert session.entries == ()


def test_session_accepts_only_semantic_entries():
    session = BattlePresentationSession()

    with pytest.raises(TypeError):
        session.record("Ser Branoc dealt damage.")
    with pytest.raises(TypeError):
        BattlePresentationSession(max_entries=True)
    with pytest.raises(ValueError):
        BattlePresentationSession(max_entries=0)


def test_transient_rejection_replaces_itself_without_consuming_history():
    session = BattlePresentationSession(max_entries=2)
    history = (_entry(1), _entry(2))
    for entry in history:
        session.record(entry)
    first = BattleLogEntry(
        BattleEventType.INPUT_REJECTED,
        rejection_reason=InputRejectionReason.TARGET_UNAVAILABLE,
    )
    second = BattleLogEntry(
        BattleEventType.INPUT_REJECTED,
        rejection_reason=InputRejectionReason.MOVE_UNAVAILABLE,
    )

    session.record_transient_rejection(first)
    session.record_transient_rejection(second)

    assert session.entries == (*history, second)

    session.begin_player_turn()
    assert session.entries == ()


def test_transient_rejection_accepts_only_typed_input_rejections():
    session = BattlePresentationSession()

    with pytest.raises(TypeError):
        session.record_transient_rejection("unavailable")
    with pytest.raises(ValueError):
        session.record_transient_rejection(_entry(1))


def test_session_owns_no_combat_state():
    session = BattlePresentationSession()

    assert set(vars(session)) == {
        "_max_entries",
        "_entries",
        "_transient_rejection",
    }

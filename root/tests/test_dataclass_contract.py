from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from app.combat.move import (
    DamageType,
    Move,
    MoveKind,
    ResourceType,
    ScalingAttribute,
    TargetType,
)
from app.combat.move_presentation import MovePresentation, MoveRole
from app.combat.result import CombatOutcome, CombatOutcomeType
from app.content.drifter_spec import DrifterStatSpec
from app.content.enemy_spec import StatBlockSpec
from app.presentation.battle_models import (
    ActionIntent,
    BattleView,
    BattleVisualView,
    CombatantView,
    EnemyCombatantView,
    InteractionPhase,
    SuperMeterView,
)
from app.ui.battle_ui import ChooseAction


ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_ROOT = ROOT / "src" / "app"
STAT_NAMES = (
    "constitution",
    "spirit",
    "intelligence",
    "strength",
    "dexterity",
    "intuition",
)


def _move(**overrides):
    values = {
        "name": "Test Move",
        "kind": MoveKind.DAMAGE,
        "resource_type": ResourceType.NONE,
        "resource_cost": 0,
        "power": 10,
        "scales_with": (ScalingAttribute.STRENGTH,),
        "accuracy": 100,
        "target": TargetType.ENEMY,
        "damage_type": DamageType.PHYSICAL,
        "mechanic": None,
        "description": "A test move.",
        "presentation": MovePresentation(MoveRole.NORMAL),
    }
    values.update(overrides)
    return Move(**values)


def _battle_view(**overrides):
    values = {
        "interaction_phase": InteractionPhase.ACTIONS,
        "player": CombatantView(
            display_name="Ser Branoc",
            hp_current=116,
            hp_maximum=116,
            mana_current=46,
            mana_maximum=46,
            super_current=10,
            super_maximum=100,
        ),
        "enemies": (
            EnemyCombatantView(
                target_id="enemy_1",
                display_label="Goblin",
                hp_current=60,
                hp_maximum=60,
            ),
        ),
        "super_meter": SuperMeterView(
            current=10,
            maximum=100,
            fill_bps=1000,
            ready=False,
            activation_key="S",
            activation_offered=False,
        ),
    }
    values.update(overrides)
    return BattleView(**values)


def _stat_spec():
    return DrifterStatSpec(
        constitution=14,
        spirit=6,
        intelligence=5,
        strength=15,
        dexterity=10,
        intuition=10,
    )


def test_production_dataclass_surface_is_exactly_audited():
    files = tuple(sorted(PRODUCTION_ROOT.rglob("*.py")))
    import_files = tuple(
        path
        for path in files
        if "from dataclasses import" in path.read_text(encoding="utf-8")
        or "import dataclasses" in path.read_text(encoding="utf-8")
    )
    texts = tuple(path.read_text(encoding="utf-8") for path in files)

    assert len(import_files) == 23
    assert sum(text.count("@dataclass") for text in texts) == 74
    assert sum(text.count("@dataclass(frozen=True)") for text in texts) == 71
    assert sum(text.count("@dataclass\n") for text in texts) == 3
    assert sum(text.count("def __post_init__(self)") for text in texts) == 58
    assert sum(text.count("field(default_factory=") for text in texts) == 1

    forbidden = (
        "asdict(",
        "astuple(",
        "fields(",
        "dataclasses.replace(",
        "is_dataclass(",
        "make_dataclass(",
        "InitVar",
        "KW_ONLY",
        "order=",
        "unsafe_hash=",
        "slots=",
        "kw_only=",
        "metadata=",
    )
    assert not any(token in text for text in texts for token in forbidden)

    metadata_files = tuple(
        path
        for path in files
        if "__dataclass_fields__" in path.read_text(encoding="utf-8")
    )
    assert {path.relative_to(ROOT).as_posix() for path in metadata_files} == {
        "src/app/content/drifter_spec.py",
        "src/app/content/enemy_spec.py",
    }


def test_required_field_metadata_is_only_ordered_name_iteration():
    assert tuple(DrifterStatSpec.__dataclass_fields__) == STAT_NAMES
    assert tuple(StatBlockSpec.__dataclass_fields__) == STAT_NAMES

    assert _stat_spec().as_dict() == {
        "constitution": 14,
        "spirit": 6,
        "intelligence": 5,
        "strength": 15,
        "dexterity": 10,
        "intuition": 10,
    }


def test_default_factory_creates_a_fresh_nested_view_value():
    first = _battle_view()
    second = _battle_view()

    assert first.visual == BattleVisualView()
    assert first.visual is not second.visual


def test_structural_equality_is_available_for_value_records():
    assert _move() == _move()
    assert _move(name="Other Move") != _move()
    assert CombatOutcome(CombatOutcomeType.BREAK_APPLIED) == CombatOutcome(
        "break_applied"
    )
    assert ChooseAction("attack") == ChooseAction(ActionIntent.ATTACK)


def test_frozen_records_reject_attribute_assignment():
    move = _move()
    outcome = CombatOutcome(CombatOutcomeType.BREAK_APPLIED)

    with pytest.raises(FrozenInstanceError):
        move.name = "Changed"
    with pytest.raises(FrozenInstanceError):
        outcome.amount = 1


def test_post_init_normalizes_values_and_enforces_validation():
    assert ChooseAction("attack").intent is ActionIntent.ATTACK
    assert _move(kind="damage").kind is MoveKind.DAMAGE
    assert _move(resource_type="none").resource_type is ResourceType.NONE

    with pytest.raises(ValueError, match="invalid action intent"):
        ChooseAction("not-an-action")
    with pytest.raises(ValueError, match="must be between 1 and 100"):
        StatBlockSpec(0, 1, 1, 1, 1, 1)


def test_nested_defaults_and_optional_values_match_dd_usage():
    move = _move(presentation=None, mechanic=None)

    assert move.scales_with == (ScalingAttribute.STRENGTH,)
    assert move.presentation is None
    assert move.mechanic is None


def test_static_audit_does_not_confuse_incidental_hash_or_repr_behavior_with_contract():
    texts = tuple(
        path.read_text(encoding="utf-8")
        for path in PRODUCTION_ROOT.rglob("*.py")
    )

    assert not any("@dataclass(order=" in text for text in texts)
    assert not any("unsafe_hash=" in text for text in texts)

"""M9E-1 deterministic identity audit coverage."""

import pytest

from app.combat.combat_state import CombatState
from app.combat.move import ResourceType
from app.combat.resolver import CombatResolver
from app.combat.result import CombatOutcomeType
from app.enemies.goblin.definition import Goblin
from app.enemies.state import EnemyState
from app.player.character import BlackMage, Brawler, Monk, RogueArcher
from app.player.player_state import PlayerState


class ScriptedRng:
    def __init__(self, *rolls):
        self.rolls = list(rolls)

    def randint(self, _start, _end):
        if not self.rolls:
            raise AssertionError("unexpected random roll")
        return self.rolls.pop(0)


def _outcome_types(result):
    return tuple(outcome.outcome_type for outcome in result.outcomes)


def _player(character_type):
    return PlayerState(character_type())


def _enemy():
    return EnemyState(Goblin())


def test_branoc_complete_brace_loop_is_durable_and_single_use():
    actor = _player(Brawler)
    target = _enemy()
    state = CombatState()
    resolver = CombatResolver(rng=ScriptedRng(1, 100, 1, 100))

    brace = resolver.resolve_move(actor, actor, "Brace", combat_state=state)
    assert brace.accepted is True
    assert actor.mana_resource.current == actor.mana_resource.maximum - 5
    assert state.brace_incoming_protection_active(actor) is True
    assert state.brace_follow_up_damage_bonus_percent(actor, "heavy_attack") == 30

    incoming = resolver.resolve_move(
        _player(Brawler),
        actor,
        "Crestgrave Reaping",
        combat_state=state,
    )
    assert incoming.accepted is True
    assert incoming.hit is True
    assert state.brace_incoming_protection_active(actor) is True

    heavy = resolver.resolve_move(
        actor,
        target,
        "Ironwake Dismemberment",
        combat_state=state,
    )
    assert heavy.accepted is True
    assert state.brace_follow_up_damage_bonus_percent(actor, "heavy_attack") == 0


@pytest.mark.parametrize(
    ("rolls", "expected_break"),
    (
        ((1, 100, 100), True),
        ((100, 100), False),
    ),
)
def test_azhvielle_gravemantle_clean_and_miss_paths(rolls, expected_break):
    actor = _player(BlackMage)
    target = _enemy()
    state = CombatState()

    gravemantle = CombatResolver(rng=ScriptedRng(*rolls)).resolve_move(
        actor,
        target,
        "Gravemantle Rupture",
        combat_state=state,
    )

    assert gravemantle.accepted is True
    assert gravemantle.hit is expected_break
    assert actor.mana_resource.current == 44
    assert state.arcane_overcharge_active(actor) is True
    assert state.gravemantle_break_active(target) is expected_break

    discharge = CombatResolver(rng=ScriptedRng(1, 100)).resolve_move(
        actor,
        target,
        "Gloamweight Sepulcher",
        combat_state=state,
    )
    assert discharge.accepted is True
    assert CombatOutcomeType.OVERCHARGE_CONSUMED in _outcome_types(discharge)
    assert state.arcane_overcharge_active(actor) is False
    assert state.gravemantle_break_active(target) is False


def test_azhvielle_backlash_is_real_risk_and_surviving_charge_is_unstable():
    actor = _player(BlackMage)
    target = _enemy()
    state = CombatState()

    result = CombatResolver(rng=ScriptedRng(1, 100, 1, 8)).resolve_move(
        actor,
        target,
        "Gravemantle Rupture",
        combat_state=state,
    )

    assert result.accepted is True
    assert CombatOutcomeType.BACKLASH_DAMAGE in _outcome_types(result)
    assert CombatOutcomeType.INSTABILITY_APPLIED in _outcome_types(result)
    assert actor.health.current < actor.health.maximum
    assert state.arcane_overcharge_active(actor) is True
    assert state.arcane_instability_active(actor) is True


def test_azhvielle_accepted_discharge_miss_consumes_all_held_state():
    actor = _player(BlackMage)
    target = _enemy()
    state = CombatState()
    state.activate_arcane_overcharge(actor, broken_target=target)
    state.activate_arcane_instability(actor)

    result = CombatResolver(rng=ScriptedRng(100)).resolve_move(
        actor,
        target,
        "Gloamweight Sepulcher",
        combat_state=state,
    )

    assert result.accepted is True
    assert result.hit is False
    assert _outcome_types(result)[:3] == (
        CombatOutcomeType.OVERCHARGE_CONSUMED,
        CombatOutcomeType.BREAK_CLEARED,
        CombatOutcomeType.INSTABILITY_CLEARED,
    )
    assert state.arcane_overcharge_active(actor) is False
    assert state.gravemantle_break_active(target) is False
    assert state.arcane_instability_active(actor) is False


def test_azhvielle_instability_only_changes_physical_incoming_damage():
    attacker = _player(Brawler)
    unstable = _player(BlackMage)
    baseline = _player(BlackMage)
    unstable_state = CombatState()
    unstable_state.activate_arcane_overcharge(unstable)
    unstable_state.activate_arcane_instability(unstable)

    physical_unstable = CombatResolver(rng=ScriptedRng(1, 100)).resolve_move(
        attacker,
        unstable,
        "Crestgrave Reaping",
        combat_state=unstable_state,
    )
    physical_baseline = CombatResolver(rng=ScriptedRng(1, 100)).resolve_move(
        _player(Brawler),
        baseline,
        "Crestgrave Reaping",
        combat_state=CombatState(),
    )

    assert physical_unstable.damage > physical_baseline.damage
    assert unstable_state.arcane_instability_physical_vulnerability_percent(unstable) == 25


@pytest.mark.parametrize(
    ("character_type", "required_moves"),
    (
        (Brawler, {"Brace", "Ironwake Dismemberment"}),
        (BlackMage, {"Gravemantle Rupture", "Scepter Sweep"}),
        (RogueArcher, {"Infused Barb"}),
        (Monk, {"Hydro Whip", "Tempest Surge", "Lightning Palm"}),
    ),
)
def test_m9e_authored_identity_moves_remain_in_the_live_roster(
    character_type,
    required_moves,
):
    player = _player(character_type)
    authored_names = {move.name for move in player.combat_moves}

    assert required_moves <= authored_names
    assert len(player.combat_moves) == 5
    assert sum(move.resource_type == ResourceType.SUPER for move in player.combat_moves) == 1


def test_m9e_no_identity_mechanics_branch_on_display_names_or_class_names():
    from pathlib import Path

    source_root = Path(__file__).parents[1] / "src" / "app"
    inspected = (
        source_root / "combat" / "battle.py",
        source_root / "combat" / "resolver.py",
        source_root / "combat" / "combat_state.py",
        source_root / "combat" / "status_state.py",
    )
    forbidden_fragments = (
        ".display_name ==",
        "__class__.__name__",
        "isinstance(actor,",
        "isinstance(target,",
        "Brawler",
        "BlackMage",
        "RogueArcher",
        "Monk",
    )

    for path in inspected:
        source = path.read_text(encoding="utf-8")
        assert not any(fragment in source for fragment in forbidden_fragments), path

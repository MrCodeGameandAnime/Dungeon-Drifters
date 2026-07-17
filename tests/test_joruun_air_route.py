from app.combat.combat_state import CombatState
from app.combat.result import CombatOutcome, CombatOutcomeType
from app.combat.resolver import CombatResolver, _mitigation, _scaled_damage_power
from app.combat.storm import LIGHTNING_PALM_MECHANIC, TEMPEST_SURGE_MECHANIC
from app.enemies.goblin.definition import Goblin
from app.enemies.state import EnemyState
from app.player.character import Monk
from app.player.player_state import PlayerState
from app.presentation.battle_models import BattleEventType, BattleLogEntry, InteractionPhase
from app.presentation.battle_presenter import BattlePresenter
from app.ui.terminal_battle_ui import TerminalBattleUI


class ScriptedRng:
    def __init__(self, *rolls):
        self.rolls = list(rolls)
        self.calls = []

    def randint(self, start, end):
        self.calls.append((start, end))
        return self.rolls.pop(0)


def _joruun():
    return PlayerState(Monk())


def _goblin():
    return EnemyState(Goblin())


def _move(actor, name):
    return next(move for move in actor.combat_moves if move.name == name)


def test_air_route_uses_stable_authored_markers():
    actor = _joruun()
    assert _move(actor, "Tempest Surge").mechanic == TEMPEST_SURGE_MECHANIC
    assert _move(actor, "Lightning Palm").mechanic == LIGHTNING_PALM_MECHANIC


def test_tempest_hit_applies_and_refreshes_turbulence_only_to_a_survivor():
    actor = _joruun()
    target = _goblin()
    state = CombatState()

    first = CombatResolver(rng=ScriptedRng(1, 100)).resolve_move(
        actor, target, "Tempest Surge", combat_state=state
    )
    second = CombatResolver(rng=ScriptedRng(1, 100)).resolve_move(
        actor, target, "Tempest Surge", combat_state=state
    )

    assert first.accepted and first.hit
    assert first.outcomes[-1].outcome_type == CombatOutcomeType.TURBULENCE_APPLIED
    assert second.outcomes[-1].outcome_type == CombatOutcomeType.TURBULENCE_REFRESHED
    assert state.turbulence_active(actor, target)


def test_tempest_miss_and_direct_defeat_apply_no_turbulence():
    actor = _joruun()
    missed_target = _goblin()
    missed_state = CombatState()
    miss = CombatResolver(rng=ScriptedRng(100)).resolve_move(
        actor, missed_target, "Tempest Surge", combat_state=missed_state
    )

    defeated_actor = _joruun()
    defeated_target = _goblin()
    defeated_target.health.take_damage(defeated_target.health.current - 1)
    defeated_state = CombatState()
    defeat = CombatResolver(rng=ScriptedRng(1, 100)).resolve_move(
        defeated_actor, defeated_target, "Tempest Surge", combat_state=defeated_state
    )

    assert miss.accepted and not miss.hit and miss.outcomes == ()
    assert not missed_state.turbulence_active(actor, missed_target)
    assert defeat.hit and not defeated_target.is_alive()
    assert not defeated_state.turbulence_active(defeated_actor, defeated_target)


def test_turbulent_lightning_uses_bonus_and_consumes_without_stun_rng():
    actor = _joruun()
    target = _goblin()
    state = CombatState()
    state.apply_turbulence(actor, target)
    rng = ScriptedRng(1, 100)

    result = CombatResolver(rng=rng).resolve_move(
        actor, target, "Lightning Palm", combat_state=state
    )
    move = _move(actor, "Lightning Palm")
    expected = max(
        1,
        _scaled_damage_power(actor, move) * 135 // 100
        - _mitigation(target, move.damage_type),
    )

    assert result.accepted and result.hit and result.damage == expected
    assert tuple(outcome.outcome_type for outcome in result.outcomes) == (
        CombatOutcomeType.TURBULENCE_CONSUMED,
    )
    assert not state.turbulence_active(actor, target)
    assert not state.stun_active(target)
    assert rng.calls == [(1, 100), (1, 100)]


def test_turbulent_lightning_miss_consumes_and_rejection_preserves():
    actor = _joruun()
    target = _goblin()
    state = CombatState()
    state.apply_turbulence(actor, target)
    miss_rng = ScriptedRng(100)

    miss = CombatResolver(rng=miss_rng).resolve_move(
        actor, target, "Lightning Palm", combat_state=state
    )
    assert miss.accepted and not miss.hit
    assert not state.turbulence_active(actor, target)
    assert miss_rng.calls == [(1, 100)]

    rejected_actor = _joruun()
    rejected_actor.mana_resource.spend(rejected_actor.mana_resource.current)
    rejected_target = _goblin()
    rejected_state = CombatState()
    rejected_state.apply_turbulence(rejected_actor, rejected_target)
    rejected_rng = ScriptedRng()
    rejected = CombatResolver(rng=rejected_rng).resolve_move(
        rejected_actor,
        rejected_target,
        "Lightning Palm",
        combat_state=rejected_state,
    )
    assert not rejected.accepted
    assert rejected_state.turbulence_active(rejected_actor, rejected_target)
    assert rejected_rng.calls == []


def test_tempest_preserves_existing_conductive_state():
    actor = _joruun()
    target = _goblin()
    state = CombatState()
    state.apply_conductive(actor, target)

    result = CombatResolver(rng=ScriptedRng(1, 100)).resolve_move(
        actor, target, "Tempest Surge", combat_state=state
    )

    assert result.hit
    assert state.conductive_active(actor, target)
    assert state.turbulence_active(actor, target)


def test_turbulence_presentation_is_dynamic_and_non_consuming():
    player = _joruun()
    enemy = _goblin()
    state = CombatState()
    state.apply_turbulence(player, enemy)
    presenter = BattlePresenter()

    view = presenter.build(
        player=player,
        enemy=enemy,
        combat_state=state,
        interaction_phase=InteractionPhase.REGULAR_MOVES,
    )
    lightning = next(move for move in view.move_options if move.selection_key == "Lightning Palm")

    assert lightning.name == "Lightning Palm"
    assert lightning.tags == ("Hybrid", "Turbulence", "7 Mana")
    assert "35% increased damage" in lightning.rules_summary
    assert "Turbulence" in view.enemy.temporary_labels
    assert state.turbulence_active(player, enemy)


def test_terminal_renders_turbulence_outcomes():
    entry = BattleLogEntry(
        event_type=BattleEventType.STATUS,
        actor_name="Joruun Veyr",
        target_name="Goblin",
        outcomes=(
            CombatOutcome(CombatOutcomeType.TURBULENCE_APPLIED),
            CombatOutcome(CombatOutcomeType.TURBULENCE_REFRESHED),
            CombatOutcome(CombatOutcomeType.TURBULENCE_CONSUMED),
        ),
    )
    assert TerminalBattleUI._outcome_lines(entry) == (
        "Goblin became surrounded by Turbulence.",
        "Goblin's Turbulence was refreshed.",
        "Joruun Veyr discharged Turbulence through Lightning Palm.",
    )

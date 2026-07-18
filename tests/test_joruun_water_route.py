from app.combat.battle import Battle
from app.combat.combat_state import CombatState
from app.combat.result import CombatOutcome, CombatOutcomeType
from app.combat.resolver import CombatResolver, _mitigation, _scaled_damage_power
from app.combat.storm import HYDRO_WHIP_MECHANIC, LIGHTNING_PALM_MECHANIC
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


def test_water_route_uses_stable_authored_markers():
    actor = _joruun()
    assert _move(actor, "Hydro Whip").mechanic == HYDRO_WHIP_MECHANIC
    assert _move(actor, "Lightning Palm").mechanic == LIGHTNING_PALM_MECHANIC


def test_hydro_hit_applies_and_refreshes_conductive_only_to_a_survivor():
    actor = _joruun()
    target = _goblin()
    state = CombatState()

    first = CombatResolver(rng=ScriptedRng(1, 100)).resolve_move(
        actor, target, "Hydro Whip", combat_state=state
    )
    second = CombatResolver(rng=ScriptedRng(1, 100)).resolve_move(
        actor, target, "Hydro Whip", combat_state=state
    )

    assert first.accepted and first.hit
    assert first.outcomes[-1].outcome_type == CombatOutcomeType.CONDUCTIVE_APPLIED
    assert second.outcomes[-1].outcome_type == CombatOutcomeType.CONDUCTIVE_REFRESHED
    assert state.conductive_active(actor, target)


def test_hydro_miss_and_direct_defeat_apply_no_conductive():
    actor = _joruun()
    missed_target = _goblin()
    missed_state = CombatState()
    miss = CombatResolver(rng=ScriptedRng(100)).resolve_move(
        actor, missed_target, "Hydro Whip", combat_state=missed_state
    )

    defeated_target = _goblin()
    defeated_target.health.take_damage(defeated_target.health.current - 1)
    defeated_state = CombatState()
    defeat = CombatResolver(rng=ScriptedRng(1, 100)).resolve_move(
        _joruun(), defeated_target, "Hydro Whip", combat_state=defeated_state
    )

    assert miss.accepted and not miss.hit and miss.outcomes == ()
    assert not missed_state.conductive_active(actor, missed_target)
    assert defeat.hit and not defeated_target.is_alive()
    assert not any(
        outcome.outcome_type == CombatOutcomeType.CONDUCTIVE_APPLIED
        for outcome in defeat.outcomes
    )


def test_conductive_lightning_uses_bonus_consumes_and_applies_stun_after_damage():
    actor = _joruun()
    target = _goblin()
    state = CombatState()
    state.apply_conductive(actor, target)
    rng = ScriptedRng(1, 100, 1)

    result = CombatResolver(rng=rng).resolve_move(
        actor, target, "Lightning Palm", combat_state=state
    )
    move = _move(actor, "Lightning Palm")
    expected = max(
        1,
        _scaled_damage_power(actor, move) * 125 // 100
        - _mitigation(target, move.damage_type),
    )

    assert result.accepted and result.hit and result.damage == expected
    assert tuple(outcome.outcome_type for outcome in result.outcomes) == (
        CombatOutcomeType.CONDUCTIVE_CONSUMED,
        CombatOutcomeType.STUN_APPLIED,
    )
    assert not state.conductive_active(actor, target)
    assert state.stun_active(target)
    assert rng.calls == [(1, 100), (1, 100), (1, 100)]


def test_conductive_lightning_miss_consumes_without_stun_rng():
    actor = _joruun()
    target = _goblin()
    state = CombatState()
    state.apply_conductive(actor, target)
    rng = ScriptedRng(100)

    result = CombatResolver(rng=rng).resolve_move(
        actor, target, "Lightning Palm", combat_state=state
    )

    assert result.accepted and not result.hit
    assert tuple(outcome.outcome_type for outcome in result.outcomes) == (
        CombatOutcomeType.CONDUCTIVE_CONSUMED,
    )
    assert not state.conductive_active(actor, target)
    assert not state.stun_active(target)
    assert rng.calls == [(1, 100)]


def test_rejected_lightning_preserves_conductive_and_uses_no_rng():
    actor = _joruun()
    actor.mana_resource.spend(actor.mana_resource.current)
    target = _goblin()
    state = CombatState()
    state.apply_conductive(actor, target)
    rng = ScriptedRng()

    result = CombatResolver(rng=rng).resolve_move(
        actor, target, "Lightning Palm", combat_state=state
    )

    assert not result.accepted and result.reason == "insufficient_mana"
    assert state.conductive_active(actor, target)
    assert rng.calls == []


def test_conductive_lightning_direct_defeat_does_not_roll_or_apply_stun():
    actor = _joruun()
    target = _goblin()
    target.health.take_damage(target.health.current - 1)
    state = CombatState()
    state.apply_conductive(actor, target)
    rng = ScriptedRng(1, 100)

    result = CombatResolver(rng=rng).resolve_move(
        actor, target, "Lightning Palm", combat_state=state
    )

    assert result.hit and not target.is_alive()
    assert not state.stun_active(target)
    assert rng.calls == [(1, 100), (1, 100)]


def test_battle_stun_skip_is_universal_and_runs_no_lifecycle():
    player = _joruun()
    enemy = _goblin()
    battle = Battle(player, enemy, ui=object())

    for source, stunned in ((player, enemy), (enemy, player)):
        battle.combat_state.apply_stun(source, stunned)
        before_turn = battle.combat_state.turn_count
        assert battle._skip_stunned_action_opportunity(stunned)
        assert battle.combat_state.turn_count == before_turn
        assert not battle.combat_state.stun_active(stunned)
        entry = battle.presentation_session.entries[-1]
        assert tuple(outcome.outcome_type for outcome in entry.outcomes) == (
            CombatOutcomeType.STUN_TRIGGERED,
            CombatOutcomeType.STUN_EXPIRED,
        )


def test_conductive_presentation_is_dynamic_and_non_consuming():
    player = _joruun()
    enemy = _goblin()
    state = CombatState()
    state.apply_conductive(player, enemy)
    presenter = BattlePresenter()

    first = presenter.build(
        player=player,
        enemy=enemy,
        combat_state=state,
        interaction_phase=InteractionPhase.REGULAR_MOVES,
    )
    second = presenter.build(
        player=player,
        enemy=enemy,
        combat_state=state,
        interaction_phase=InteractionPhase.REGULAR_MOVES,
    )
    lightning = next(move for move in first.move_options if move.selection_key == "Lightning Palm")

    assert first == second
    assert lightning.name == "Lightning Palm"
    assert lightning.tags == ("Hybrid", "Conductive", "7 Mana")
    assert "25% increased damage" in lightning.rules_summary
    assert "35% chance to Stun" in lightning.rules_summary
    assert "Conductive" in first.enemy.temporary_labels
    assert state.conductive_active(player, enemy)


def test_terminal_renders_conductive_and_stun_outcomes():
    entry = BattleLogEntry(
        event_type=BattleEventType.STATUS,
        actor_name="Joruun Veyr",
        target_name="Goblin",
        outcomes=(
            CombatOutcome(CombatOutcomeType.CONDUCTIVE_APPLIED),
            CombatOutcome(CombatOutcomeType.CONDUCTIVE_CONSUMED),
            CombatOutcome(CombatOutcomeType.STUN_APPLIED),
        ),
    )
    assert TerminalBattleUI._outcome_lines(entry) == (
        "Goblin became Conductive.",
        "Joruun Veyr discharged Conductive through Lightning Palm.",
        "Goblin was Stunned.",
    )

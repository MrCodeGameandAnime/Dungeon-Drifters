import inspect

import app.combat.resolver as resolver_module
from app.combat.cinderwrit import INFUSED_BARB_MECHANIC
from app.combat.combat_state import CombatState
from app.combat.move import (
    DamageType,
    Move,
    MoveKind,
    ResourceType,
    ScalingAttribute,
    TargetType,
)
from app.combat.resolver import CombatResolver
from app.combat.result import CombatOutcomeTarget, CombatOutcomeType
from app.enemies.goblin.definition import Goblin
from app.enemies.state import EnemyState
from app.player.character import Brawler, RogueArcher
from app.player.character_run_state import (
    CINDERWRIT_PREPARATION_COST,
    CharacterRunState,
    InfusionKind,
    PreparedPayloadId,
    RunItemId,
)
from app.player.player_state import PlayerState


class ScriptedRng:
    def __init__(self, *rolls):
        self.rolls = list(rolls)
        self.calls = []

    def randint(self, start, end):
        self.calls.append((start, end))
        if not self.rolls:
            raise AssertionError("unexpected random roll")
        return self.rolls.pop(0)


def _prepare_cinderwrit(run_state):
    run_state.prepare_payload(
        PreparedPayloadId.CINDERWRIT,
        CINDERWRIT_PREPARATION_COST,
    )
    return run_state


def _resolve_cinderwrit(actor, target, combat_state, run_state, *rolls):
    rng = ScriptedRng(*rolls)
    result = CombatResolver(rng=rng).resolve_move(
        actor,
        target,
        "Infused Barb",
        combat_state=combat_state,
        character_run_state=run_state,
    )
    return result, rng


def _prepare_poison_infusion(run_state):
    run_state.prepare_infusion(
        InfusionKind.POISON,
        {
            RunItemId.DEEP_COAL: 1,
            RunItemId.NIGHT_BERRY: 1,
        },
    )
    return run_state


def test_authored_cinderwrit_contract_preserves_existing_combat_values():
    move = next(
        move
        for move in PlayerState(RogueArcher()).combat_moves
        if move.mechanic == INFUSED_BARB_MECHANIC
    )

    assert move.name == "Infused Barb"
    assert move.kind == MoveKind.DAMAGE
    assert move.resource_type == ResourceType.MANA
    assert move.resource_cost == 5
    assert move.power == 14
    assert move.scales_with == (
        ScalingAttribute.INTUITION,
        ScalingAttribute.INTELLIGENCE,
    )
    assert move.accuracy == 88
    assert move.target == TargetType.ENEMY
    assert move.damage_type == DamageType.MAGICAL


def test_unprepared_cinderwrit_is_rejected_before_mana_rng_or_state_mutation():
    actor = PlayerState(RogueArcher())
    target = EnemyState(Goblin())
    combat_state = CombatState()
    run_state = actor.character_run_state
    mana_before = actor.mana_resource.current
    target_hp_before = target.health.current
    rng = ScriptedRng()

    result = CombatResolver(rng=rng).resolve_move(
        actor,
        target,
        "Infused Barb",
        combat_state=combat_state,
        character_run_state=run_state,
    )

    assert result.accepted is False
    assert result.reason == "infused_barb_unprepared"
    assert result.outcomes == ()
    assert actor.mana_resource.current == mana_before
    assert run_state.payload_prepared(PreparedPayloadId.CINDERWRIT) is False
    assert target.health.current == target_hp_before
    assert combat_state.burn_active(target) is False
    assert rng.calls == []


def test_unaffordable_cinderwrit_preserves_prepared_payload_and_uses_no_rng():
    actor = PlayerState(RogueArcher())
    target = EnemyState(Goblin())
    combat_state = CombatState()
    run_state = _prepare_cinderwrit(actor.character_run_state)
    actor.mana_resource.spend(actor.mana_resource.current)
    rng = ScriptedRng()

    result = CombatResolver(rng=rng).resolve_move(
        actor,
        target,
        "Infused Barb",
        combat_state=combat_state,
        character_run_state=run_state,
    )

    assert result.accepted is False
    assert result.reason == "insufficient_mana"
    assert run_state.payload_prepared(PreparedPayloadId.CINDERWRIT) is True
    assert actor.mana_resource.current == 0
    assert rng.calls == []


def test_invalid_target_state_and_run_state_preserve_payload_and_mana():
    actor = PlayerState(RogueArcher())
    target = EnemyState(Goblin())
    combat_state = CombatState()
    run_state = _prepare_cinderwrit(actor.character_run_state)
    mana_before = actor.mana_resource.current

    invalid_target = CombatResolver(rng=ScriptedRng()).resolve_move(
        actor,
        actor,
        "Infused Barb",
        combat_state=combat_state,
        character_run_state=run_state,
    )
    invalid_combat_state = CombatResolver(rng=ScriptedRng()).resolve_move(
        actor,
        target,
        "Infused Barb",
        character_run_state=run_state,
    )
    invalid_run_state = CombatResolver(rng=ScriptedRng()).resolve_move(
        actor,
        target,
        "Infused Barb",
        combat_state=combat_state,
    )

    assert invalid_target.reason == "invalid_target_type"
    assert invalid_combat_state.reason == "invalid_combat_state"
    assert invalid_run_state.reason == "invalid_character_run_state"
    assert run_state.payload_prepared(PreparedPayloadId.CINDERWRIT) is True
    assert actor.mana_resource.current == mana_before
    assert combat_state.burn_active(target) is False


def test_accepted_hit_spends_mana_consumes_payload_and_applies_exact_target_burn():
    actor = PlayerState(RogueArcher())
    target = EnemyState(Goblin())
    other_target = EnemyState(Goblin())
    combat_state = CombatState()
    run_state = _prepare_cinderwrit(actor.character_run_state)
    mana_before = actor.mana_resource.current
    target_hp_before = target.health.current

    result, rng = _resolve_cinderwrit(
        actor,
        target,
        combat_state,
        run_state,
        1,
        100,
    )

    assert result.accepted is True
    assert result.hit is True
    assert result.damage == target_hp_before - target.health.current
    assert result.damage > 0
    assert result.resource_spent == 5
    assert actor.mana_resource.current == mana_before - 5
    assert run_state.payload_prepared(PreparedPayloadId.CINDERWRIT) is False
    assert tuple(outcome.outcome_type for outcome in result.outcomes) == (
        CombatOutcomeType.INFUSED_BARB_CONSUMED,
        CombatOutcomeType.BURN_APPLIED,
    )
    assert result.outcomes[0].target == CombatOutcomeTarget.ACTOR
    assert result.outcomes[1].target == CombatOutcomeTarget.TARGET
    burn = combat_state.burn_status(target)
    assert burn.source is actor
    assert burn.target is target
    assert burn.remaining_ticks == 3
    assert burn.damage_per_tick == 7
    assert combat_state.burn_active(other_target) is False
    assert rng.calls == [(1, 100), (1, 100)]


def test_accepted_hit_routes_poison_infusion_to_standard_poison():
    actor = PlayerState(RogueArcher())
    target = EnemyState(Goblin())
    combat_state = CombatState()
    run_state = _prepare_poison_infusion(actor.character_run_state)

    result, _ = _resolve_cinderwrit(
        actor,
        target,
        combat_state,
        run_state,
        1,
        100,
    )

    assert result.accepted is True
    assert result.hit is True
    assert tuple(outcome.outcome_type for outcome in result.outcomes) == (
        CombatOutcomeType.INFUSED_BARB_CONSUMED,
        CombatOutcomeType.POISON_APPLIED,
    )
    assert combat_state.poison_active(target) is True
    assert combat_state.burn_active(target) is False
    assert combat_state.poison_status(target).remaining_ticks == 4
    assert combat_state.poison_status(target).damage_per_tick == 5


def test_accepted_miss_spends_mana_and_payload_without_applying_burn():
    actor = PlayerState(RogueArcher())
    target = EnemyState(Goblin())
    combat_state = CombatState()
    run_state = _prepare_cinderwrit(actor.character_run_state)
    mana_before = actor.mana_resource.current
    super_before = actor.super_resource.current
    target_hp_before = target.health.current

    result, rng = _resolve_cinderwrit(
        actor,
        target,
        combat_state,
        run_state,
        100,
    )

    assert result.accepted is True
    assert result.hit is False
    assert result.damage == 0
    assert result.resource_spent == 5
    assert tuple(outcome.outcome_type for outcome in result.outcomes) == (
        CombatOutcomeType.INFUSED_BARB_CONSUMED,
    )
    assert actor.mana_resource.current == mana_before - 5
    assert actor.super_resource.current == super_before
    assert run_state.payload_prepared(PreparedPayloadId.CINDERWRIT) is False
    assert target.health.current == target_hp_before
    assert combat_state.burn_active(target) is False
    assert rng.calls == [(1, 100)]


def test_direct_defeat_consumes_payload_without_creating_dead_target_burn():
    actor = PlayerState(RogueArcher())
    target = EnemyState(Goblin())
    target.health.take_damage(target.health.current - 1)
    combat_state = CombatState()
    run_state = _prepare_cinderwrit(actor.character_run_state)

    result, _ = _resolve_cinderwrit(
        actor,
        target,
        combat_state,
        run_state,
        1,
        100,
    )

    assert result.accepted is True
    assert target.is_alive() is False
    assert tuple(outcome.outcome_type for outcome in result.outcomes) == (
        CombatOutcomeType.INFUSED_BARB_CONSUMED,
    )
    assert combat_state.burn_active(target) is False


def test_landed_hit_refreshes_existing_burn_after_payload_consumption():
    actor = PlayerState(RogueArcher())
    target = EnemyState(Goblin())
    combat_state = CombatState()
    combat_state.apply_burn(actor, target)
    combat_state.complete_accepted_action(target, (actor,))
    run_state = _prepare_cinderwrit(actor.character_run_state)

    result, _ = _resolve_cinderwrit(
        actor,
        target,
        combat_state,
        run_state,
        1,
        100,
    )

    assert tuple(outcome.outcome_type for outcome in result.outcomes) == (
        CombatOutcomeType.INFUSED_BARB_CONSUMED,
        CombatOutcomeType.BURN_REFRESHED,
    )
    assert combat_state.burn_status(target).remaining_ticks == 3


def test_mechanic_marker_not_move_or_character_name_controls_integration():
    actor = PlayerState(Brawler())
    move = Move(
        name="Prepared Shot",
        kind=MoveKind.DAMAGE,
        resource_type=ResourceType.NONE,
        resource_cost=0,
        power=5,
        scales_with=(ScalingAttribute.INTELLIGENCE,),
        accuracy=100,
        target=TargetType.ENEMY,
        damage_type=DamageType.MAGICAL,
        mechanic=INFUSED_BARB_MECHANIC,
        description="A test prepared shot.",
    )
    actor.character.combat_moves.append(move)
    target = EnemyState(Goblin())
    combat_state = CombatState()
    run_state = CharacterRunState(
        prepared_payloads={PreparedPayloadId.CINDERWRIT: InfusionKind.FIRE}
    )

    result = CombatResolver(rng=ScriptedRng(1, 100)).resolve_move(
        actor,
        target,
        move.name,
        combat_state=combat_state,
        character_run_state=run_state,
    )

    assert result.accepted is True
    assert run_state.payload_prepared(PreparedPayloadId.CINDERWRIT) is False
    assert combat_state.burn_active(target) is True


def test_cinderwrit_marker_is_rejected_on_non_damage_moves_without_consumption():
    actor = PlayerState(Brawler())
    move = Move(
        name="Prepared Recovery",
        kind=MoveKind.HEALING,
        resource_type=ResourceType.NONE,
        resource_cost=0,
        power=5,
        scales_with=(ScalingAttribute.NONE,),
        accuracy=100,
        target=TargetType.SELF,
        damage_type=DamageType.HEALING,
        mechanic=INFUSED_BARB_MECHANIC,
        description="A malformed prepared action.",
    )
    actor.character.combat_moves.append(move)
    run_state = CharacterRunState(
        prepared_payloads={PreparedPayloadId.CINDERWRIT: InfusionKind.FIRE}
    )
    rng = ScriptedRng()

    result = CombatResolver(rng=rng).resolve_move(
        actor,
        actor,
        move.name,
        combat_state=CombatState(),
        character_run_state=run_state,
    )

    assert result.accepted is False
    assert result.reason == "unsupported_mechanic"
    assert run_state.payload_prepared(PreparedPayloadId.CINDERWRIT) is True
    assert rng.calls == []


def test_resolver_owns_no_player_game_or_display_name_lookup_for_cinderwrit():
    source = inspect.getsource(resolver_module)

    assert "PlayerState" not in source
    assert "GameState" not in source
    assert "RogueArcher" not in source
    assert "Infused Barb" not in source

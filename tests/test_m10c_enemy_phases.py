import pytest

from app.combat.battle import Battle
from app.combat.combat_state import CombatState
from app.combat.result import MoveResult
from app.enemies.goblin.definition import Goblin
from app.enemies.state import EnemyState
from app.player.character import BlackMage, Brawler
from app.player.player_state import PlayerState
from app.presentation.battle_models import BattleEventType, InteractionPhase
from app.ui.terminal_battle_ui import TerminalBattleUI


def _result(*, accepted=True):
    return MoveResult(
        accepted=accepted,
        hit=accepted,
        move_name="Slash",
        resource_spent=0,
        damage=0,
        healing=0,
        statuses_applied=(),
        reason=None if accepted else "rejected",
    )


class RecordingRng:
    def __init__(self, initiative=1):
        self.initiative = initiative
        self.randint_calls = []
        self.choice_calls = []

    def randint(self, start, end):
        self.randint_calls.append((start, end))
        return self.initiative

    def choice(self, options):
        options = tuple(options)
        self.choice_calls.append(options)
        return options[0]


class RecordingResolver:
    def __init__(self, *, accepted=True, before_result=None):
        self.accepted = accepted
        self.before_result = before_result
        self.calls = []

    def resolve_move(self, actor, target, move_name, **kwargs):
        self.calls.append((actor, target, move_name, kwargs))
        if self.before_result is not None:
            self.before_result(actor, target, len(self.calls))
        return _result(accepted=self.accepted)


class RecordingUI:
    def __init__(self):
        self.views = []
        self.read_count = 0

    def render(self, view):
        self.views.append(view)

    def read_input(self, _view):
        self.read_count += 1
        raise AssertionError("no input is expected")


class OrdinaryPlayerOpportunity(Exception):
    pass


class SentinelUI(RecordingUI):
    def read_input(self, _view):
        self.read_count += 1
        raise OrdinaryPlayerOpportunity


def _enemies(count):
    return tuple(EnemyState(Goblin()) for _ in range(count))


def _battle(count=4, *, resolver=None, rng=None, ui=None):
    return Battle(
        PlayerState(Brawler()),
        _enemies(count),
        ui=ui or RecordingUI(),
        resolver=resolver or RecordingResolver(),
        rng=rng or RecordingRng(),
    )


def test_player_action_plus_four_enemy_actions_advances_five_lifecycles():
    resolver = RecordingResolver()
    battle = _battle(resolver=resolver)

    battle._complete_accepted_action(
        battle.player_state,
        battle.enemies,
        _result(),
    )
    battle.enemy_phase()

    assert tuple(call[0] for call in resolver.calls) == battle.enemies
    assert all(call[1] is battle.player_state for call in resolver.calls)
    assert battle.combat_state.turn_count == 5


def test_enemy_phase_skips_defeated_enemy_without_renumbering_or_opportunity():
    resolver = RecordingResolver()
    battle = _battle(resolver=resolver)
    battle.enemies[1].health.take_damage(battle.enemies[1].health.maximum)

    battle.enemy_phase()

    assert tuple(call[0] for call in resolver.calls) == (
        battle.enemies[0],
        battle.enemies[2],
        battle.enemies[3],
    )
    assert battle.enemy_target_ids == ("enemy_1", "enemy_2", "enemy_3", "enemy_4")
    assert battle.combat_state.turn_count == 3


def test_suppressed_enemy_preserves_protection_until_next_accepted_enemy_action():
    observations = []

    def observe_protection(actor, target, call_number):
        observations.append(
            (
                actor,
                call_number,
                battle.combat_state.is_defending(target),
                battle.combat_state.brace_incoming_protection_active(target),
            )
        )

    resolver = RecordingResolver(before_result=observe_protection)
    battle = _battle(count=3, resolver=resolver)
    player = battle.player_state
    battle.combat_state.activate_defend(player)
    battle.combat_state.activate_brace(player)
    battle.combat_state.apply_frozen(player, battle.enemies[0])

    battle.enemy_phase()

    assert tuple(item[0] for item in observations) == battle.enemies[1:]
    assert observations[0][2:] == (True, True)
    assert observations[1][2:] == (False, False)
    assert battle.combat_state.turn_count == 2
    assert not battle.combat_state.frozen_active(battle.enemies[0])
    assert battle.combat_state.brace_follow_up_damage_bonus_percent(
        player,
        "heavy_attack",
    ) > 0


def test_frozen_then_stun_suppress_consecutive_enemy_phases_without_lifecycle():
    resolver = RecordingResolver()
    battle = _battle(count=2, resolver=resolver)
    player = battle.player_state
    enemy = battle.enemies[0]
    battle.enemies[1].health.take_damage(battle.enemies[1].health.current)
    battle.combat_state.apply_frozen(player, enemy)
    battle.combat_state.apply_stun(player, enemy)
    battle.combat_state.apply_burn(player, enemy)
    battle.combat_state.apply_poison(player, enemy)
    battle.combat_state.apply_frostbite(
        player,
        enemy,
        damage_per_tick=5,
        ticks=3,
    )
    battle.combat_state.start_heal_cooldown(enemy)
    hp_before = enemy.health.current
    mana_before = enemy.mana_resource.current
    super_before = enemy.super_resource.current

    battle.enemy_phase()

    assert not battle.combat_state.frozen_active(enemy)
    assert battle.combat_state.stun_active(enemy)
    assert resolver.calls == []
    assert battle.combat_state.turn_count == 0
    assert battle.combat_state.heal_cooldown_remaining(enemy) == 3
    assert enemy.health.current == hp_before
    assert enemy.mana_resource.current == mana_before
    assert enemy.super_resource.current == super_before

    battle.enemy_phase()

    assert not battle.combat_state.stun_active(enemy)
    assert resolver.calls == []
    assert battle.combat_state.turn_count == 0
    assert battle.combat_state.heal_cooldown_remaining(enemy) == 3
    assert enemy.health.current == hp_before
    assert enemy.mana_resource.current == mana_before
    assert enemy.super_resource.current == super_before

    battle.enemy_phase()

    assert len(resolver.calls) == 1
    assert battle.combat_state.turn_count == 1
    assert battle.combat_state.heal_cooldown_remaining(enemy) == 2
    assert enemy.health.current < hp_before


def test_enemy_resolver_rejection_is_invariant_failure_without_lifecycle_or_retry():
    resolver = RecordingResolver(accepted=False)
    rng = RecordingRng()
    battle = _battle(resolver=resolver, rng=rng)

    with pytest.raises(RuntimeError, match="enemy resolver rejected"):
        battle.enemy_phase()

    assert len(resolver.calls) == 1
    assert len(rng.choice_calls) == 1
    assert battle.combat_state.turn_count == 0


def test_enemy_phase_stops_immediately_when_player_dies():
    def defeat_player(_actor, target, _call_number):
        target.health.take_damage(target.health.current)

    resolver = RecordingResolver(before_result=defeat_player)
    battle = _battle(resolver=resolver)

    battle.enemy_phase()

    assert len(resolver.calls) == 1
    assert resolver.calls[0][0] is battle.enemies[0]
    assert battle._winner() == "enemy"
    assert battle.combat_state.turn_count == 1


def test_winner_rule_requires_all_enemies_and_preserves_simultaneous_death_defeat():
    battle = _battle(count=2)

    battle.enemies[0].health.take_damage(battle.enemies[0].health.current)
    assert battle._winner() is None

    battle.enemies[1].health.take_damage(battle.enemies[1].health.current)
    assert battle._winner() == "player"

    battle.player_state.health.take_damage(battle.player_state.health.current)
    assert battle._winner() == "enemy"


def test_run_uses_side_initiative_and_enemy_phase_stops_after_lethal_first_action():
    def defeat_player(_actor, target, _call_number):
        target.health.take_damage(target.health.current)

    rng = RecordingRng(initiative=2)
    resolver = RecordingResolver(before_result=defeat_player)
    ui = RecordingUI()
    battle = _battle(resolver=resolver, rng=rng, ui=ui)

    assert battle.run() == "enemy"

    assert rng.randint_calls == [(1, 2)]
    assert len(resolver.calls) == 1
    initiative = next(
        entry
        for entry in battle.presentation_session.entries
        if entry.event_type == BattleEventType.INITIATIVE
    )
    assert initiative.actor_name == "Enemy side"


def test_suppressed_player_is_followed_by_complete_living_enemy_phase():
    resolver = RecordingResolver()
    rng = RecordingRng(initiative=1)
    ui = SentinelUI()
    battle = _battle(resolver=resolver, rng=rng, ui=ui)
    player = battle.player_state
    battle.combat_state.apply_frozen(battle.enemies[0], player)
    battle.combat_state.apply_burn(battle.enemies[0], player)
    battle.combat_state.apply_poison(battle.enemies[1], player)
    battle.combat_state.apply_frostbite(
        battle.enemies[2],
        player,
        damage_per_tick=5,
        ticks=3,
    )
    battle.combat_state.start_heal_cooldown(player)
    hp_before = player.health.current
    mana_before = player.mana_resource.current
    super_before = player.super_resource.current
    burn_before = battle.combat_state.burn_status(player)
    poison_before = battle.combat_state.poison_status(player)
    frostbite_before = battle.combat_state.frostbite_status(player)

    with pytest.raises(OrdinaryPlayerOpportunity):
        battle.run()

    assert rng.randint_calls == [(1, 2)]
    assert tuple(call[0] for call in resolver.calls) == battle.enemies
    assert all(call[1] is player for call in resolver.calls)
    assert len(rng.choice_calls) == len(battle.enemies)
    assert ui.read_count == 1
    assert not battle.combat_state.frozen_active(player)
    assert battle.combat_state.turn_count == len(battle.enemies)
    assert battle.combat_state.heal_cooldown_remaining(player) == 3
    assert battle.combat_state.burn_status(player) is burn_before
    assert battle.combat_state.poison_status(player) is poison_before
    assert battle.combat_state.frostbite_status(player) is frostbite_before
    assert player.health.current == hp_before
    assert player.mana_resource.current == mana_before
    assert player.super_resource.current == super_before


def test_final_view_is_complete_inactive_and_requires_no_input():
    ui = RecordingUI()
    battle = _battle(count=2, ui=ui)

    def defeat_enemies():
        for enemy in battle.enemies:
            enemy.health.take_damage(enemy.health.current)
        battle.combat_state.complete_accepted_action(
            battle.player_state,
            battle.enemies,
        )
        return True

    battle.player_action = defeat_enemies

    assert battle.run() == "player"

    final = ui.views[-1]
    assert final.interaction_phase == InteractionPhase.COMPLETE
    assert final.action_options == ()
    assert final.move_options == ()
    assert final.target_options == ()
    assert final.inventory_items == ()
    assert final.super_meter.activation_offered is False
    assert tuple(enemy.temporary_labels for enemy in final.enemies) == (
        ("Defeated",),
        ("Defeated",),
    )
    assert ui.read_count == 0

    lines = []
    TerminalBattleUI(
        output_func=lines.append,
        width_provider=lambda: 80,
        unicode_enabled=False,
        ansi_enabled=False,
        interactive=False,
    ).render(final)
    rendered = "\n".join(lines)
    assert "ACTIONS" not in rendered
    assert "[A] Attack" not in rendered
    assert "0. Back" not in rendered
    terminal = TerminalBattleUI(
        output_func=lambda _line: None,
        input_func=lambda _prompt: "attack",
        unicode_enabled=False,
        ansi_enabled=False,
        interactive=False,
    )
    assert terminal._translate_choice(final, "attack") is None
    assert terminal._translate_choice(final, "super") is None
    assert terminal._translate_choice(final, "back") is None


def test_defeated_combatant_cleanup_removes_owned_state_and_preserves_living_state():
    state = CombatState()
    defeated = PlayerState(BlackMage())
    living_owner = PlayerState(BlackMage())
    linked_target = EnemyState(Goblin())
    unrelated_target = EnemyState(Goblin())

    state.activate_defend(defeated)
    state.activate_brace(defeated)
    state.start_heal_cooldown(defeated)
    state.activate_arcane_overcharge(defeated, broken_target=linked_target)
    state.activate_arcane_instability(defeated)
    state.apply_conductive(defeated, linked_target)
    state.apply_turbulence(living_owner, defeated)
    state.apply_frost_charge(living_owner, defeated)
    state.apply_frozen(living_owner, defeated)
    state.apply_frostbite(
        living_owner,
        defeated,
        damage_per_tick=5,
        ticks=3,
    )

    state.activate_arcane_overcharge(living_owner, broken_target=defeated)
    state.activate_arcane_instability(living_owner)
    state.apply_conductive(living_owner, unrelated_target)
    defeated.health.take_damage(defeated.health.current)

    state.clear_defeated_combatant(defeated)

    assert not state.is_defending(defeated)
    assert not state.brace_incoming_protection_active(defeated)
    assert state.brace_follow_up_damage_bonus_percent(defeated, "heavy_attack") == 0
    assert state.heal_cooldown_remaining(defeated) == 0
    assert not state.arcane_overcharge_active(defeated)
    assert not state.arcane_instability_active(defeated)
    assert not state.gravemantle_break_active(defeated)
    assert state.active_status_kinds(defeated) == ()
    assert not state.conductive_active(defeated, linked_target)
    assert not state.turbulence_active(living_owner, defeated)

    assert state.arcane_overcharge_active(living_owner)
    assert state.arcane_instability_active(living_owner)
    assert state.conductive_active(living_owner, unrelated_target)


def test_lethal_frostbite_lifecycle_clears_all_non_status_temporary_state():
    state = CombatState()
    actor = PlayerState(BlackMage())
    source = EnemyState(Goblin())
    actor.health.take_damage(actor.health.current - 5)
    state.activate_defend(actor)
    state.activate_brace(actor)
    state.start_heal_cooldown(actor)
    state.activate_arcane_overcharge(actor, broken_target=source)
    state.activate_arcane_instability(actor)
    state.apply_frostbite(source, actor, damage_per_tick=5, ticks=3)

    state.complete_accepted_action(actor, (source,))

    assert not actor.is_alive()
    assert not state.is_defending(actor)
    assert not state.brace_incoming_protection_active(actor)
    assert state.brace_follow_up_damage_bonus_percent(actor, "heavy_attack") == 0
    assert state.heal_cooldown_remaining(actor) == 0
    assert not state.arcane_overcharge_active(actor)
    assert not state.arcane_instability_active(actor)
    assert state.active_status_kinds(actor) == ()
    assert state.turn_count == 1

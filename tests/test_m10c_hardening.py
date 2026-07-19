import pytest

from app.combat.battle import Battle
from app.combat.combat_state import CombatState
from app.combat.resolver import CombatResolver
from app.combat.result import CombatOutcomeType
from app.enemies.goblin.definition import Goblin
from app.enemies.state import EnemyState
from app.game.encounter_manifest import create_route_encounter_enemies
from app.player.character import BlackMage, Brawler, Monk, RogueArcher
from app.player.inventory_action import InventoryActionResolver
from app.player.player_state import PlayerState
from app.presentation.battle_models import ActionIntent, InteractionPhase
from app.ui.battle_ui import ChooseAction, ChooseMove, ChooseTarget


class AlwaysOneRng:
    def randint(self, _start, _end):
        return 1

    def choice(self, options):
        return tuple(options)[0]


class ScriptedBattleUI:
    def __init__(self, inputs):
        self.inputs = iter(inputs)
        self.views = []

    def render(self, view):
        self.views.append(view)

    def read_input(self, _view):
        return next(self.inputs)


ENCOUNTER_COMPOSITIONS = {
    "surface_goblin_solo": ("goblin",),
    "surface_goblin_pair": ("goblin", "goblin"),
    "surface_warrior_solo": ("goblin_warrior",),
    "surface_warrior_pair": ("goblin_warrior", "goblin_warrior"),
    "surface_shaman_solo": ("goblin_shaman",),
    "surface_shaman_pair": ("goblin_shaman", "goblin_shaman"),
    "surface_elite_patrol": ("goblin_elite", "goblin"),
    "surface_goblin_lord": ("goblin_lord", "goblin", "goblin_warrior"),
}


@pytest.mark.parametrize("node_id, expected_ids", ENCOUNTER_COMPOSITIONS.items())
def test_every_authored_composition_is_ready_for_real_battle(node_id, expected_ids):
    enemies = create_route_encounter_enemies(node_id)
    battle = Battle(
        PlayerState(Brawler()),
        enemies,
        ui=ScriptedBattleUI(()),
        resolver=CombatResolver(rng=AlwaysOneRng()),
        rng=AlwaysOneRng(),
    )

    assert tuple(enemy.archetype_id for enemy in battle.enemies) == expected_ids
    assert battle.enemies == enemies
    assert len({id(enemy) for enemy in battle.enemies}) == len(enemies)


def test_real_two_goblin_target_flow_keeps_labels_and_requires_both_defeats():
    first, second = EnemyState(Goblin()), EnemyState(Goblin())
    first.health.take_damage(first.health.current - 1)
    second.health.take_damage(second.health.current - 1)
    ui = ScriptedBattleUI(
        (
            ChooseAction(ActionIntent.ATTACK),
            ChooseMove("Crestgrave Reaping"),
            ChooseTarget("enemy_2"),
            ChooseAction(ActionIntent.ATTACK),
            ChooseMove("Crestgrave Reaping"),
        )
    )
    battle = Battle(
        PlayerState(Brawler()),
        (first, second),
        ui=ui,
        resolver=CombatResolver(rng=AlwaysOneRng()),
        rng=AlwaysOneRng(),
    )

    assert battle.run() == "player"

    assert first.health.current == 0
    assert second.health.current == 0
    assert battle.enemy_display_labels == ("Goblin 1", "Goblin 2")
    assert battle.enemy_target_ids == ("enemy_1", "enemy_2")
    final = ui.views[-1]
    assert final.interaction_phase is InteractionPhase.COMPLETE
    assert tuple(enemy.display_label for enemy in final.enemies) == (
        "Goblin 1",
        "Goblin 2",
    )
    assert tuple(enemy.temporary_labels for enemy in final.enemies) == (
        ("Defeated",),
        ("Defeated",),
    )
    target_view = next(
        view for view in ui.views if view.interaction_phase is InteractionPhase.TARGETS
    )
    assert tuple(option.display_label for option in target_view.target_options) == (
        "Goblin 1",
        "Goblin 2",
    )


def test_branoc_follow_up_damage_targets_one_of_two_enemies():
    actor = PlayerState(Brawler())
    first, second = EnemyState(Goblin()), EnemyState(Goblin())
    state = CombatState()
    resolver = CombatResolver(rng=AlwaysOneRng())

    assert resolver.resolve_move(actor, actor, "Brace", combat_state=state).accepted
    result = resolver.resolve_move(
        actor,
        second,
        "Ironwake Dismemberment",
        combat_state=state,
    )

    assert result.accepted and result.hit
    assert first.health.current == first.health.maximum
    assert second.health.current < second.health.maximum
    assert state.brace_follow_up_damage_bonus_percent(actor, "heavy_attack") == 0


def test_azhvielle_overcharge_consumes_linked_break_without_leaking_to_other_enemy():
    actor = PlayerState(BlackMage())
    first, second = EnemyState(Goblin()), EnemyState(Goblin())
    state = CombatState()
    state.activate_arcane_overcharge(actor, broken_target=first)

    result = CombatResolver(rng=AlwaysOneRng()).resolve_move(
        actor,
        second,
        "Gloamweight Sepulcher",
        combat_state=state,
    )

    assert result.accepted and result.hit
    assert first.health.current == first.health.maximum
    assert second.health.current < second.health.maximum
    assert not state.gravemantle_break_active(first)
    assert not state.gravemantle_break_active(second)
    assert not state.arcane_overcharge_active(actor)


def test_zhaivra_infusion_applies_burn_to_the_exact_selected_enemy():
    actor = PlayerState(RogueArcher())
    first, second = EnemyState(Goblin()), EnemyState(Goblin())
    state = CombatState()
    preparation = InventoryActionResolver().resolve(
        "prepare_fire_infusion",
        actor.character_run_state,
    )
    result = CombatResolver(rng=AlwaysOneRng()).resolve_move(
        actor,
        second,
        "Infused Barb",
        combat_state=state,
        character_run_state=actor.character_run_state,
    )

    assert preparation.accepted
    assert result.accepted and result.hit
    assert state.burn_active(second)
    assert not state.burn_active(first)
    assert first.health.current == first.health.maximum


def test_joruun_setup_remains_linked_when_lightning_palm_targets_another_enemy():
    actor = PlayerState(Monk())
    first, second = EnemyState(Goblin()), EnemyState(Goblin())
    state = CombatState()
    resolver = CombatResolver(rng=AlwaysOneRng())

    hydro = resolver.resolve_move(actor, first, "Hydro Whip", combat_state=state)
    tempest = resolver.resolve_move(actor, first, "Tempest Surge", combat_state=state)
    palm = resolver.resolve_move(actor, second, "Lightning Palm", combat_state=state)

    assert hydro.accepted and hydro.hit
    assert tempest.accepted and tempest.hit
    assert palm.accepted and palm.hit
    assert palm.move_name == "Lightning Palm"
    assert state.conductive_active(actor, first)
    assert state.turbulence_active(actor, first)
    assert not state.conductive_active(actor, second)
    assert not state.turbulence_active(actor, second)
    assert CombatOutcomeType.LIGHTNING_STORM_TRIGGERED not in tuple(
        outcome.outcome_type for outcome in palm.outcomes
    )

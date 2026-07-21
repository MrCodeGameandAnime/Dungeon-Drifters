from app.combat.battle import Battle
from app.combat.combat_state import CombatState
from app.enemies.factory import create_enemy_state
from app.enemies.goblin.definition import Goblin
from app.enemies.state import EnemyState
from app.game.game_state import GameState
from app.game.overworld_session import OverworldSession, OverworldSessionResult
from app.game.overworld_state import ContextualRoutePhase
from app.game.save_repository import SaveRepository
from app.player.character import Brawler, RogueArcher
from app.player.character_run_state import (
    FIRE_INFUSION_REQUIREMENTS,
    InfusionKind,
)
from app.player.player_state import PlayerState
from app.presentation.overworld_models import OverworldAction
from app.ui.overworld_ui import ChooseOverworldAction


class NoInputBattleUI:
    def render(self, _view):
        pass

    def read_input(self, _view):
        raise AssertionError("this test does not enter Battle input")


class ScriptedOverworldUI:
    def __init__(self, inputs):
        self.inputs = list(inputs)
        self.views = []

    def render(self, view):
        self.views.append(view)

    def read_input(self, _view):
        return self.inputs.pop(0)


class SequenceBattleFactory:
    def __init__(self, winners, mutations=()):
        self.winners = tuple(winners)
        self.mutations = tuple(mutations)
        self.instances = []

    def __call__(self, player_state, enemies, *, ui, encounter_label):
        index = len(self.instances)
        factory = self

        class SequenceBattle:
            def __init__(self):
                self.player_state = player_state
                self.enemies = tuple(enemies)
                self.ui = ui
                self.encounter_label = encounter_label
                self.state_during_run = None

            def run(self):
                if index < len(factory.mutations):
                    factory.mutations[index](self.player_state)
                self.state_during_run = self.player_state.snapshot()
                winner = factory.winners[index]
                if winner == "player":
                    for enemy in self.enemies:
                        enemy.health.take_damage(enemy.health.current)
                return winner

        battle = SequenceBattle()
        self.instances.append(battle)
        return battle


def _quit_inputs():
    return (
        ChooseOverworldAction(OverworldAction.OPTIONS),
        ChooseOverworldAction(OverworldAction.QUIT),
        ChooseOverworldAction(OverworldAction.CONFIRM),
    )


def _session(game, inputs, battles, tmp_path):
    return OverworldSession(
        game,
        ui=ScriptedOverworldUI(inputs),
        battle_factory=battles,
        enemy_factory=create_enemy_state,
        battle_ui_factory=NoInputBattleUI,
        save_repository=SaveRepository(tmp_path / "dungeon_drifters.json"),
    )


def _advance_to_goblin_lord(game):
    game.overworld_state.begin_surface_route()
    completed_encounters = (
        "surface_goblin_solo",
        "surface_goblin_pair",
        "surface_warrior_solo",
        "surface_warrior_pair",
        "surface_shaman_solo",
        "surface_shaman_pair",
        "surface_elite_patrol",
    )
    for encounter_id in completed_encounters:
        game.world_state.mark_encounter_defeated(encounter_id)
    for rest_id in (
        "surface_rest_after_warrior_solo",
        "surface_rest_after_shaman_pair",
        "surface_rest_before_goblin_lord",
    ):
        game.overworld_state.record_resolved_rest_node(rest_id)

    for node_id, phase in (
        ("surface_goblin_pair", ContextualRoutePhase.NONE),
        ("surface_warrior_solo", ContextualRoutePhase.ENTER_ENCOUNTER),
        ("surface_rest_after_warrior_solo", ContextualRoutePhase.NONE),
        ("surface_warrior_pair", ContextualRoutePhase.ENTER_ENCOUNTER),
        ("surface_shaman_solo", ContextualRoutePhase.ENTER_ENCOUNTER),
        ("surface_shaman_pair", ContextualRoutePhase.ENTER_ENCOUNTER),
        ("surface_rest_after_shaman_pair", ContextualRoutePhase.NONE),
        ("surface_elite_patrol", ContextualRoutePhase.ENTER_ENCOUNTER),
        ("surface_rest_before_goblin_lord", ContextualRoutePhase.NONE),
        ("surface_goblin_lord", ContextualRoutePhase.ENTER_ENCOUNTER),
    ):
        game.overworld_state.advance_to(node_id, contextual_phase=phase)


def test_finished_real_battle_starts_next_battle_with_fresh_combat_state():
    player = PlayerState(RogueArcher())
    player.health.take_damage(9)
    player.mana_resource.spend(6)
    player.super_resource.gain(21)
    player.character_run_state.prepare_infusion(
        InfusionKind.FIRE,
        FIRE_INFUSION_REQUIREMENTS,
    )
    persistent_before = player.snapshot()

    first, second = EnemyState(Goblin()), EnemyState(Goblin())
    first_battle = Battle(
        player,
        (first, second),
        ui=NoInputBattleUI(),
    )
    state = first_battle.combat_state

    state.activate_defend(first)
    state.activate_brace(first)
    state.start_heal_cooldown(first)
    state.activate_arcane_overcharge(player, broken_target=first)
    state.activate_arcane_instability(player)
    state.apply_burn(player, first)
    state.apply_poison(player, first)
    state.apply_frost_charge(player, first)
    state.apply_frozen(player, first)
    state.apply_stun(player, first)
    state.apply_frostbite(player, first, damage_per_tick=5, ticks=3)
    state.apply_conductive(player, first)
    state.apply_turbulence(player, first)
    state.apply_conductive(player, second)
    second.health.take_damage(1)

    first.health.take_damage(first.health.current)
    state.clear_defeated_combatant(first)

    assert state.active_status_kinds(first) == ()
    assert not state.is_defending(first)
    assert not state.brace_incoming_protection_active(first)
    assert state.brace_follow_up_damage_bonus_percent(first, "heavy_attack") == 0
    assert state.heal_cooldown_remaining(first) == 0
    assert not state.burn_active(first)
    assert not state.poison_active(first)
    assert not state.frostbite_active(first)
    assert state.frost_charge_count(player, first) == 0
    assert not state.conductive_active(player, first)
    assert not state.turbulence_active(player, first)
    assert state.conductive_active(player, second)
    assert state.arcane_overcharge_active(player)
    assert not state.gravemantle_break_active(first)

    next_enemy = EnemyState(Goblin())
    second_battle = Battle(
        player,
        (next_enemy,),
        ui=NoInputBattleUI(),
    )
    next_state = second_battle.combat_state

    assert second_battle is not first_battle
    assert next_state is not state
    assert next_state.turn_count == 0
    assert next_state.active_status_kinds(player) == ()
    assert next_state.active_status_kinds(next_enemy) == ()
    assert not next_state.is_defending(player)
    assert not next_state.brace_incoming_protection_active(player)
    assert next_state.heal_cooldown_remaining(player) == 0
    assert not next_state.arcane_overcharge_active(player)
    assert not next_state.conductive_active(player, next_enemy)
    assert not next_state.turbulence_active(player, next_enemy)
    assert player.snapshot() == persistent_before
    assert player.character_run_state.prepared_infusion() is InfusionKind.FIRE
    assert second is not next_enemy


def test_pair_defeat_retry_restores_player_and_pays_reward_once(tmp_path):
    player = PlayerState(Brawler(), gold=11)
    player.health.take_damage(9)
    player.mana_resource.spend(4)
    player.super_resource.gain(17)
    before = player.snapshot()
    game = GameState(player)
    game.overworld_state.advance_to(
        "surface_goblin_pair",
        contextual_phase=ContextualRoutePhase.ENTER_ENCOUNTER,
    )
    battles = SequenceBattleFactory(
        ("enemy", "player"),
        (
            lambda acting_player: (
                acting_player.health.take_damage(33),
                acting_player.mana_resource.spend(8),
                acting_player.super_resource.gain(50),
            ),
        ),
    )
    ui = ScriptedOverworldUI(
        (
            ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER),
            ChooseOverworldAction(OverworldAction.RETRY),
            *_quit_inputs(),
        )
    )
    session = OverworldSession(
        game,
        ui=ui,
        battle_factory=battles,
        enemy_factory=create_enemy_state,
        battle_ui_factory=NoInputBattleUI,
        save_repository=SaveRepository(tmp_path / "dungeon_drifters.json"),
    )

    assert session.run() is OverworldSessionResult.QUIT
    assert len(battles.instances) == 2
    first, retry = battles.instances
    assert first.player_state is player
    assert retry.player_state is player
    assert len(first.enemies) == len(retry.enemies) == 2
    assert all(
        first_enemy is not retry_enemy
        for first_enemy, retry_enemy in zip(first.enemies, retry.enemies)
    )
    assert first.state_during_run != before
    assert player.health.current == before["resources"]["health"]["current"]
    assert player.mana_resource.current == before["resources"]["mana"]["current"]
    assert player.super_resource.current == before["resources"]["super"]["current"]
    assert player.exp_state.current == 80
    assert player.level_state.current == 1
    assert player.growth_points == 0
    assert player.gold == 17
    assert game.world_state.defeated_encounters == ("surface_goblin_pair",)
    assert game.overworld_state.current_route_node_id == "surface_warrior_solo"
    assert ui.views[1].contextual_route_option.action is OverworldAction.RETRY


def test_goblin_lord_defeat_retry_reaches_dungeon_and_pays_once(tmp_path):
    player = PlayerState(Brawler(), gold=7)
    player.health.take_damage(6)
    player.mana_resource.spend(3)
    player.super_resource.gain(12)
    before = player.snapshot()
    game = GameState(player)
    _advance_to_goblin_lord(game)
    def mutate(acting_player):
        acting_player.health.take_damage(31)
        acting_player.mana_resource.spend(7)
        acting_player.super_resource.gain(40)

    battles = SequenceBattleFactory(("enemy", "player"), (mutate,))
    ui = ScriptedOverworldUI(
        (
            ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER),
            ChooseOverworldAction(OverworldAction.RETRY),
            *_quit_inputs(),
        )
    )
    session = OverworldSession(
        game,
        ui=ui,
        battle_factory=battles,
        enemy_factory=create_enemy_state,
        battle_ui_factory=NoInputBattleUI,
        save_repository=SaveRepository(tmp_path / "dungeon_drifters.json"),
    )

    assert session.run() is OverworldSessionResult.QUIT
    assert len(battles.instances) == 2
    first, retry = battles.instances
    assert tuple(enemy.archetype_id for enemy in first.enemies) == (
        "goblin_lord",
        "goblin",
        "goblin_warrior",
    )
    assert tuple(enemy.archetype_id for enemy in retry.enemies) == (
        "goblin_lord",
        "goblin",
        "goblin_warrior",
    )
    assert all(
        first_enemy is not retry_enemy
        for first_enemy, retry_enemy in zip(first.enemies, retry.enemies)
    )
    assert first.state_during_run != before
    assert player.super_resource.current == before["resources"]["super"]["current"]
    assert player.health.current - before["resources"]["health"]["current"] == (
        player.health.maximum - before["resources"]["health"]["maximum"]
    )
    assert player.mana_resource.current - before["resources"]["mana"]["current"] == (
        player.mana_resource.maximum - before["resources"]["mana"]["maximum"]
    )
    assert player.character.permanent_stats.as_dict() == before["attributes"]
    assert player.gold == before["gold"] + 18
    assert game.world_state.defeated_encounters.count("surface_goblin_lord") == 1
    assert game.overworld_state.current_route_node_id == "surface_dungeon_entrance"
    assert game.overworld_state.route_complete is True
    assert game.overworld_state.dungeon_entrance_reached is True
    assert game.overworld_state.resolved_rest_node_ids == (
        "surface_rest_after_warrior_solo",
        "surface_rest_after_shaman_pair",
        "surface_rest_before_goblin_lord",
    )
    assert ui.views[1].contextual_route_option.action is OverworldAction.RETRY

from app.combat.battle import Battle
from app.combat.combat_state import CombatState
from app.combat.resolver import CombatResolver
from app.enemies.factory import create_enemy_state
from app.enemies.goblin.definition import Goblin
from app.enemies.state import EnemyState
from app.game.game_state import GameState
from app.game.overworld_session import OverworldSession, OverworldSessionResult
from app.game.overworld_state import ContextualRoutePhase
from app.game.save_repository import SaveRepository
from app.player.character import BlackMage, Brawler, RogueArcher
from app.player.inventory_action import InventoryActionResolver
from app.player.character_run_state import (
    FIRE_INFUSION_REQUIREMENTS,
    InfusionKind,
)
from app.player.player_state import PlayerState
from app.presentation.battle_models import (
    ActionIntent,
    BattleEventType,
    InteractionPhase,
)
from app.presentation.overworld_models import OverworldAction
from app.ui.battle_ui import ChooseAction, ChooseMove, ChooseTarget
from app.ui.overworld_ui import ChooseOverworldAction


class NoInputBattleUI:
    def __init__(self):
        self.views = []

    def render(self, _view):
        self.views.append(_view)

    def read_input(self, _view):
        raise AssertionError("this test does not enter Battle input")


class ScriptedBattleUI:
    def __init__(self, *inputs):
        self.inputs = list(inputs)
        self.views = []

    def render(self, view):
        self.views.append(view)

    def read_input(self, _view):
        return self.inputs.pop(0)


class AlwaysOneRng:
    def __init__(self, *, initiative=1):
        self.initiative = initiative
        self._first_roll = True
        self.randint_calls = []
        self.choice_calls = []

    def randint(self, start, end):
        self.randint_calls.append((start, end))
        if self._first_roll and (start, end) == (1, 2):
            self._first_roll = False
            return self.initiative
        self._first_roll = False
        return 1

    def choice(self, options):
        options = tuple(options)
        self.choice_calls.append(options)
        return options[0]


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


def test_real_battle_run_cleans_defeated_state_and_finishes_inactive():
    player = PlayerState(Brawler())
    first, second = EnemyState(Goblin()), EnemyState(Goblin())
    first.health.take_damage(first.health.current - 1)
    second.health.take_damage(second.health.current - 1)
    rng = AlwaysOneRng()
    ui = ScriptedBattleUI(
        ChooseAction(ActionIntent.ATTACK),
        ChooseMove(player.combat_moves[0].name),
        ChooseTarget("enemy_1"),
        ChooseAction(ActionIntent.ATTACK),
        ChooseMove(player.combat_moves[0].name),
        ChooseTarget("enemy_2"),
    )
    battle = Battle(
        player,
        (first, second),
        ui=ui,
        rng=rng,
        resolver=CombatResolver(rng=rng),
        encounter_label="Goblin Pair",
    )
    state = battle.combat_state
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

    assert battle.run() == "player"

    intermediate = next(
        view
        for view in ui.views
        if view.enemies[0].defeated and not view.enemies[1].defeated
    )
    assert tuple(enemy.display_label for enemy in intermediate.enemies) == (
        "Goblin 1",
        "Goblin 2",
    )
    assert tuple(enemy.target_id for enemy in intermediate.enemies) == (
        "enemy_1",
        "enemy_2",
    )
    assert intermediate.enemies[0].hp_current == 0
    assert intermediate.enemies[0].temporary_labels == ("Defeated",)
    assert intermediate.enemies[1].hp_current > 0

    final = ui.views[-1]
    assert final.interaction_phase is InteractionPhase.COMPLETE
    assert final.action_options == ()
    assert final.move_options == ()
    assert final.target_options == ()
    assert final.inventory_items == ()
    assert all(enemy.defeated for enemy in final.enemies)
    assert tuple(enemy.temporary_labels for enemy in final.enemies) == (
        ("Defeated",),
        ("Defeated",),
    )
    assert any(
        entry.target_name == "Goblin 2"
        for entry in battle.presentation_session.entries
        if entry.event_type == BattleEventType.DAMAGE
    )
    assert any(
        entry.actor_name == "Goblin 2"
        for entry in intermediate.log_entries
    )
    assert state.active_status_kinds(first) == ()
    assert not state.is_defending(first)
    assert not state.brace_incoming_protection_active(first)
    assert state.heal_cooldown_remaining(first) == 0
    assert not state.burn_active(first)
    assert not state.poison_active(first)
    assert not state.frostbite_active(first)
    assert not state.gravemantle_break_active(first)
    assert state.arcane_overcharge_active(player)


def test_real_session_discards_completed_battle_and_next_battle_is_fresh(tmp_path):
    player = PlayerState(Brawler())
    game = GameState(player)

    class RealBattleFactory:
        def __init__(self):
            self.battles = []

        def __call__(self, player_state, enemies, *, ui, encounter_label):
            for enemy in enemies:
                enemy.health.take_damage(enemy.health.current - 1)
            battle = Battle(
                player_state,
                enemies,
                ui=ui,
                rng=AlwaysOneRng(),
                encounter_label=encounter_label,
            )
            self.battles.append(battle)
            return battle

    class BattleUIFactory:
        def __init__(self):
            self.uis = []

        def __call__(self):
            ui = ScriptedBattleUI(
                ChooseAction(ActionIntent.ATTACK),
                ChooseMove("Crestgrave Reaping"),
            )
            self.uis.append(ui)
            return ui

    battles = RealBattleFactory()
    battle_uis = BattleUIFactory()
    ui = ScriptedOverworldUI(
        (
            ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER),
            *_quit_inputs(),
        )
    )
    session = OverworldSession(
        game,
        ui=ui,
        battle_factory=battles,
        enemy_factory=create_enemy_state,
        battle_ui_factory=battle_uis,
        save_repository=SaveRepository(tmp_path / "dungeon_drifters.json"),
    )

    assert session.run() is OverworldSessionResult.QUIT
    battle = battles.battles[0]
    assert battle.interaction_phase is InteractionPhase.COMPLETE
    assert "battle" not in vars(session)
    assert all(value is not battle for value in vars(session).values())

    next_battle = Battle(
        player,
        EnemyState(Goblin()),
        ui=NoInputBattleUI(),
        rng=AlwaysOneRng(),
    )
    assert next_battle.combat_state is not battle.combat_state
    assert next_battle.combat_state.turn_count == 0
    assert next_battle is not battle


def test_real_solo_defeat_boundary_restores_before_retry_and_rewards_once(tmp_path):
    player = PlayerState(Brawler(), gold=9)
    player.health.take_damage(player.health.current - 1)
    before = player.snapshot()
    game = GameState(player)
    observed_defeat = []

    class RealBattleFactory:
        def __init__(self):
            self.battles = []

        def __call__(self, player_state, enemies, *, ui, encounter_label):
            index = len(self.battles)
            if index == 1:
                enemies[0].health.take_damage(enemies[0].health.current - 1)
            battle = Battle(
                player_state,
                enemies,
                ui=ui,
                rng=AlwaysOneRng(initiative=2 if index == 0 else 1),
                encounter_label=encounter_label,
            )
            self.battles.append(battle)
            return battle

    class BattleUIFactory:
        def __init__(self):
            self.uis = []

        def __call__(self):
            if not self.uis:
                ui = NoInputBattleUI()
            else:
                ui = ScriptedBattleUI(
                    ChooseAction(ActionIntent.ATTACK),
                    ChooseMove(player.combat_moves[0].name),
                )
            self.uis.append(ui)
            return ui

    class ObserveRetryUI(ScriptedOverworldUI):
        def read_input(self, view):
            if (
                view.contextual_route_option is not None
                and view.contextual_route_option.action is OverworldAction.RETRY
            ):
                observed_defeat.append(
                    (
                        player.snapshot(),
                        game.overworld_state.snapshot(),
                        game.world_state.snapshot(),
                    )
                )
            return super().read_input(view)

    battle_factory = RealBattleFactory()
    battle_ui_factory = BattleUIFactory()
    ui = ObserveRetryUI(
        (
            ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER),
            ChooseOverworldAction(OverworldAction.RETRY),
            *_quit_inputs(),
        )
    )
    session = OverworldSession(
        game,
        ui=ui,
        battle_factory=battle_factory,
        enemy_factory=create_enemy_state,
        battle_ui_factory=battle_ui_factory,
        save_repository=SaveRepository(tmp_path / "dungeon_drifters.json"),
    )

    assert session.run() is OverworldSessionResult.QUIT
    assert len(observed_defeat) == 1
    defeat_player, defeat_overworld, defeat_world = observed_defeat[0]
    assert defeat_player == before
    assert defeat_overworld["current_route_node_id"] == "surface_goblin_solo"
    assert defeat_overworld["current_contextual_route_phase"] == "retry"
    assert defeat_world["defeated_encounters"] == []
    assert len(battle_factory.battles) == 2
    first, retry = battle_factory.battles
    assert first.interaction_phase is InteractionPhase.COMPLETE
    assert retry.interaction_phase is InteractionPhase.COMPLETE
    assert first.enemies[0] is not retry.enemies[0]
    assert player.exp_state.current == 40
    assert player.gold == 12
    assert game.world_state.defeated_encounters == ("surface_goblin_solo",)
    assert game.overworld_state.current_route_node_id == "surface_goblin_pair"


def test_different_target_overcharge_and_break_are_encounter_local():
    actor = PlayerState(BlackMage())
    broken_target, other_target = EnemyState(Goblin()), EnemyState(Goblin())
    state = CombatState()
    state.activate_arcane_overcharge(actor, broken_target=broken_target)
    assert state.gravemantle_break_active(broken_target)
    assert not state.gravemantle_break_active(other_target)

    result = CombatResolver(rng=AlwaysOneRng()).resolve_move(
        actor,
        other_target,
        "Gloamweight Sepulcher",
        combat_state=state,
    )

    assert result.accepted and result.hit
    assert broken_target.health.current == broken_target.health.maximum
    assert other_target.health.current < other_target.health.maximum
    assert not state.gravemantle_break_active(broken_target)
    assert not state.gravemantle_break_active(other_target)
    assert not state.arcane_overcharge_active(actor)


def test_accepted_infusion_consumption_does_not_survive_into_next_battle():
    player = PlayerState(RogueArcher())
    preparation = InventoryActionResolver().resolve(
        "prepare_fire_infusion",
        player.character_run_state,
    )
    assert preparation.accepted
    assert player.character_run_state.prepared_infusion() is InfusionKind.FIRE

    first_battle = Battle(
        player,
        EnemyState(Goblin()),
        ui=ScriptedBattleUI(
            ChooseAction(ActionIntent.ATTACK),
            ChooseMove("Infused Barb"),
        ),
        rng=AlwaysOneRng(),
    )
    assert first_battle.player_action() is True
    assert player.character_run_state.prepared_infusion() is None

    next_battle = Battle(
        player,
        EnemyState(Goblin()),
        ui=NoInputBattleUI(),
        rng=AlwaysOneRng(),
    )
    assert next_battle.player_state is player
    assert player.character_run_state.prepared_infusion() is None


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

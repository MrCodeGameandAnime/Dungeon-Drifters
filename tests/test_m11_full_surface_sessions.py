import json

import pytest

from app.combat.battle import Battle
from app.combat.result import MoveResult
from app.enemies.factory import create_enemy_state
from app.game.game_state import GameState
from app.game.overworld_session import OverworldSession, OverworldSessionResult
from app.game.save_repository import SaveRepository
from app.player.character import BlackMage, Brawler, Monk, RogueArcher
from app.player.player_state import PlayerState
from app.presentation.overworld_models import OverworldAction, OverworldScreen
from app.presentation.overworld_presenter import OverworldPresenter
from app.ui.battle_ui import ChooseAction, ChooseMove, ChooseTarget
from app.ui.overworld_ui import ChooseOverworldAction


EXPECTED_COMPOSITIONS = (
    ("goblin",),
    ("goblin", "goblin"),
    ("goblin_warrior",),
    ("goblin_warrior", "goblin_warrior"),
    ("goblin_shaman",),
    ("goblin_shaman", "goblin_shaman"),
    ("goblin_elite", "goblin"),
    ("goblin_lord", "goblin", "goblin_warrior"),
)

EXPECTED_ENCOUNTER_IDS = (
    "surface_goblin_solo",
    "surface_goblin_pair",
    "surface_warrior_solo",
    "surface_warrior_pair",
    "surface_shaman_solo",
    "surface_shaman_pair",
    "surface_elite_patrol",
    "surface_goblin_lord",
)

EXPECTED_REST_IDS = (
    "surface_rest_after_warrior_solo",
    "surface_rest_after_shaman_pair",
    "surface_rest_before_goblin_lord",
)


class DeterministicRng:
    def __init__(self):
        self._first_roll = True

    def randint(self, start, end):
        if self._first_roll and (start, end) == (1, 2):
            self._first_roll = False
            return 1
        self._first_roll = False
        return 1

    def choice(self, options):
        return tuple(options)[0]


class DeterministicResolver:
    def resolve_move(
        self,
        actor,
        target,
        move_name,
        *,
        combat_state=None,
        character_run_state=None,
    ):
        del combat_state, character_run_state
        damage = 0
        if hasattr(target, "archetype_id") and target.is_alive():
            damage = target.health.current
            target.health.take_damage(damage)
        return MoveResult(
            accepted=True,
            hit=True,
            move_name=move_name,
            resource_spent=0,
            damage=damage,
            healing=0,
            statuses_applied=(),
            reason=None,
        )


class AutomaticBattleUI:
    def __init__(self):
        self.views = []

    def render(self, view):
        self.views.append(view)

    def read_input(self, view):
        if view.interaction_phase.value == "actions":
            return ChooseAction("attack")
        if view.interaction_phase.value == "regular_moves":
            return ChooseMove(view.move_options[0].selection_key)
        if view.interaction_phase.value == "targets":
            return ChooseTarget(
                next(option.target_id for option in view.target_options if option.enabled)
            )
        raise AssertionError(f"unexpected Battle phase: {view.interaction_phase!r}")


class RouteUI:
    def __init__(self, rest_actions):
        self._rest_actions = iter(rest_actions)
        self.views = []
        self.rest_decisions = []

    def render(self, view):
        self.views.append(view)

    def read_input(self, view):
        if view.screen is OverworldScreen.REST:
            action = next(self._rest_actions)
            self.rest_decisions.append((view.location_label, action))
            return ChooseOverworldAction(action)
        if view.screen is OverworldScreen.MAIN:
            if view.contextual_route_option is not None:
                return ChooseOverworldAction(view.contextual_route_option.action)
            return ChooseOverworldAction(OverworldAction.OPTIONS)
        if view.screen is OverworldScreen.OPTIONS:
            return ChooseOverworldAction(OverworldAction.QUIT)
        if view.screen is OverworldScreen.QUIT_CONFIRMATION:
            return ChooseOverworldAction(OverworldAction.CONFIRM)
        raise AssertionError(f"unexpected Overworld screen: {view.screen!r}")


class DeterministicBattleFactory:
    def __init__(self):
        self.battles = []
        self.uis = []

    def __call__(self, player_state, enemies, *, ui, encounter_label):
        battle = Battle(
            player_state,
            enemies,
            ui=ui,
            resolver=DeterministicResolver(),
            rng=DeterministicRng(),
            encounter_label=encounter_label,
        )
        self.battles.append(battle)
        self.uis.append(ui)
        return battle


@pytest.mark.parametrize(
    ("character_type", "rest_actions"),
    (
        (Brawler, (OverworldAction.REST,) * 3),
        (BlackMage, (OverworldAction.SKIP_REST,) * 3),
        (RogueArcher, (OverworldAction.REST, OverworldAction.SKIP_REST, OverworldAction.REST)),
        (Monk, (OverworldAction.SKIP_REST, OverworldAction.REST, OverworldAction.SKIP_REST)),
    ),
)
def test_four_drifters_complete_the_full_surface_route(
    character_type,
    rest_actions,
    tmp_path,
):
    player = PlayerState(character_type())
    character = player.character
    health = player.health
    mana = player.mana_resource
    super_resource = player.super_resource
    inventory = player.inventory
    run_state = player.character_run_state
    equipped_weapon = player.get_equipped("weapon")
    game = GameState(player)
    battle_factory = DeterministicBattleFactory()
    battle_ui_factory = AutomaticBattleUI
    route_ui = RouteUI(rest_actions)

    session = OverworldSession(
        game,
        ui=route_ui,
        battle_factory=battle_factory,
        enemy_factory=create_enemy_state,
        battle_ui_factory=battle_ui_factory,
        save_repository=SaveRepository(tmp_path / "dungeon_drifters.json"),
    )

    assert session.run() is OverworldSessionResult.QUIT

    assert session.game_state is game
    assert game.player_state is player
    assert player.character is character
    assert player.health is health
    assert player.mana_resource is mana
    assert player.super_resource is super_resource
    assert player.inventory is inventory
    assert player.character_run_state is run_state
    assert player.get_equipped("weapon") is equipped_weapon

    assert tuple(
        tuple(enemy.archetype_id for enemy in battle.enemies)
        for battle in battle_factory.battles
    ) == EXPECTED_COMPOSITIONS
    assert tuple(
        battle.encounter_label for battle in battle_factory.battles
    ) == (
        "Goblin Ambush",
        "Goblin Pair",
        "Goblin Warrior",
        "Warrior Patrol",
        "Goblin Shaman",
        "Shaman Pair",
        "Elite Patrol",
        "Goblin Lord",
    )
    runtime_enemies = [
        enemy
        for battle in battle_factory.battles
        for enemy in battle.enemies
    ]
    assert len(runtime_enemies) == 14
    assert len({id(enemy) for enemy in runtime_enemies}) == 14
    assert all(battle.player_state is player for battle in battle_factory.battles)
    assert all(
        battle.interaction_phase.value == "complete"
        and battle.ui.views[-1].interaction_phase.value == "complete"
        and battle.ui.views[-1].action_options == ()
        and battle.ui.views[-1].move_options == ()
        and battle.ui.views[-1].target_options == ()
        for battle in battle_factory.battles
    )

    assert game.world_state.defeated_encounters == EXPECTED_ENCOUNTER_IDS
    assert game.overworld_state.resolved_rest_node_ids == EXPECTED_REST_IDS
    assert game.overworld_state.current_route_node_id == "surface_dungeon_entrance"
    assert game.overworld_state.route_complete is True
    assert game.overworld_state.dungeon_entrance_reached is True
    assert game.overworld_state.current_contextual_route_phase.value == "none"
    assert tuple(label for label, _action in route_ui.rest_decisions) == (
        "Woodland Rest",
        "Ritual Clearing Rest",
        "Final Approach Rest",
    )
    assert tuple(action for _label, action in route_ui.rest_decisions) == rest_actions
    assert player.level_state.current == 9
    assert player.exp_state.current == 68
    assert player.growth_points == 24
    assert player.gold == 75
    assert route_ui.views[-1].contextual_route_option is None

    presenter = OverworldPresenter()
    for screen in (
        OverworldScreen.CHARACTER,
        OverworldScreen.SKILLS,
        OverworldScreen.WEAPON,
        OverworldScreen.EQUIPMENT,
        OverworldScreen.ITEMS,
        OverworldScreen.MAP,
    ):
        view = presenter.build(game, screen=screen)
        assert view.screen is screen

    serialized = json.dumps(game.snapshot(), sort_keys=True)
    assert serialized

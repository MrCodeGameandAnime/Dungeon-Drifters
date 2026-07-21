import json

import pytest

from app.combat.battle import Battle
from app.combat.resolver import CombatResolver
from app.combat.result import MoveResult
from app.enemies.factory import create_enemy_state
from app.game.game_state import GameState
from app.game.overworld_session import OverworldSession, OverworldSessionResult
from app.game.save_repository import SaveRepository
from app.player.character import BlackMage, Brawler, Monk, RogueArcher
from app.player.inventory_action import InventoryActionResolver
from app.player.player_state import PlayerState
from app.presentation.battle_models import (
    ActionIntent,
    BattleEventType,
    BattleLogEntry,
    InteractionPhase,
)
from app.presentation.overworld_models import OverworldAction, OverworldScreen
from app.presentation.overworld_presenter import OverworldPresenter
from app.ui.battle_ui import ChooseAction, ChooseMove, ChooseTarget, GoBack
from app.ui.overworld_ui import ChooseOverworldAction
from app.ui.terminal_battle_ui import TerminalBattleUI


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

EXPECTED_SIGNATURE_WIELDERS = {
    "Brawler": "Branoc",
    "Black Mage": "Azhvielle",
    "Rogue Archer": "Zhaivra",
    "Monk": "Joruun",
}


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


class SequenceRng:
    def __init__(self, *rolls):
        self.rolls = list(rolls)

    def randint(self, _start, _end):
        return self.rolls.pop(0) if self.rolls else 1

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


class RecordingCombatResolver(CombatResolver):
    def __init__(self, *, rng):
        super().__init__(rng=rng)
        self.calls = []

    def resolve_move(self, actor, target, move_name, **kwargs):
        self.calls.append((actor, target, move_name))
        return super().resolve_move(actor, target, move_name, **kwargs)


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


class ScriptedBattleUI:
    def __init__(self, *inputs):
        self.inputs = list(inputs)
        self.views = []

    def render(self, view):
        self.views.append(view)

    def read_input(self, _view):
        return self.inputs.pop(0)


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
        OverworldScreen.OPTIONS,
    ):
        before_view_snapshot = game.snapshot()
        view = presenter.build(game, screen=screen)
        assert view.screen is screen
        assert game.snapshot() == before_view_snapshot

        if screen is OverworldScreen.CHARACTER:
            assert view.character.display_name == player.character.full_display_name
            assert view.character.level == 9
            assert view.character.exp_current == 68
            assert view.character.hp_current == player.health.current
            assert view.character.mana_current == player.mana_resource.current
            assert view.character.super_current == player.super_resource.current
            assert tuple(row.label for row in view.character.stats) == (
                "Strength",
                "Constitution",
                "Intelligence",
                "Spirit",
                "Dexterity",
                "Intuition",
            )
        elif screen is OverworldScreen.SKILLS:
            assert view.skills.growth_points_available == 24
            assert tuple(row.value for row in view.skills.stats) == tuple(
                player.character.permanent_stats.as_dict()[name]
                for name in (
                    "strength",
                    "constitution",
                    "intelligence",
                    "spirit",
                    "dexterity",
                    "intuition",
                )
            )
            assert all(row.increase_enabled for row in view.skills.stats)
        elif screen is OverworldScreen.WEAPON:
            assert view.weapon.name == equipped_weapon.name
            assert view.weapon.intended_wielder == EXPECTED_SIGNATURE_WIELDERS[
                player.character.archetype_name
            ]
        elif screen is OverworldScreen.EQUIPMENT:
            assert view.equipment.necklace.item_name == "Empty"
            assert view.equipment.ring.item_name == "Empty"
            assert view.equipment.benefits == ("None",)
        elif screen is OverworldScreen.ITEMS:
            assert view.inventory is not None
            assert all(item.display_name for item in view.inventory.items)
        elif screen is OverworldScreen.MAP:
            assert view.route_map is not None
            assert view.route_map.nodes[-1].state.value == "current"
        elif screen is OverworldScreen.OPTIONS:
            assert tuple(option.action for option in view.options) == (
                OverworldAction.SAVE,
                OverworldAction.QUIT,
                OverworldAction.LOAD,
                OverworldAction.BACK,
            )
            assert view.options[1].enabled is True

    serialized = json.dumps(game.snapshot(), sort_keys=True)
    assert serialized


def test_real_battle_covers_branoc_mechanics_and_universal_defend():
    player = PlayerState(Brawler())
    battle = Battle(
        player,
        create_enemy_state("goblin"),
        ui=ScriptedBattleUI(ChooseAction(ActionIntent.DEFEND)),
        resolver=CombatResolver(rng=SequenceRng(1)),
        rng=SequenceRng(1),
    )

    assert battle.player_action() is True
    assert battle.combat_state.is_defending(player)
    assert battle.combat_state.turn_count == 1


def test_real_battle_covers_azhvielle_break_and_overcharge():
    player = PlayerState(BlackMage())
    enemy = create_enemy_state("goblin")
    rng = SequenceRng(1, 100)
    battle = Battle(
        player,
        enemy,
        ui=ScriptedBattleUI(
            ChooseAction(ActionIntent.ATTACK),
            ChooseMove("Gravemantle Rupture"),
        ),
        resolver=CombatResolver(rng=rng),
        rng=rng,
    )

    assert battle.player_action() is True
    assert battle.combat_state.gravemantle_break_active(enemy)
    assert battle.combat_state.arcane_overcharge_active(player)


def test_real_battle_covers_zhaivra_consumed_infusion_and_burn():
    player = PlayerState(RogueArcher())
    preparation = InventoryActionResolver().resolve(
        "prepare_fire_infusion",
        player.character_run_state,
    )
    assert preparation.accepted
    enemy = create_enemy_state("goblin")
    rng = SequenceRng(1, 100)
    battle = Battle(
        player,
        enemy,
        ui=ScriptedBattleUI(
            ChooseAction(ActionIntent.ATTACK),
            ChooseMove("Infused Barb"),
        ),
        resolver=CombatResolver(rng=rng),
        rng=rng,
    )

    assert battle.player_action() is True
    assert battle.combat_state.burn_active(enemy)
    assert player.character_run_state.prepared_infusion() is None


def test_real_battle_covers_joruun_target_specific_lightning_storm():
    player = PlayerState(Monk())
    first, second = create_enemy_state("goblin"), create_enemy_state("goblin")
    rng = SequenceRng(1, 100, 1, 100, 1, 100)

    class JoruunMechanicUI(ScriptedBattleUI):
        def __init__(self):
            super().__init__()
            self.moves = iter(("Hydro Whip", "Tempest Surge", "Lightning Palm"))

        def read_input(self, view):
            if view.interaction_phase is InteractionPhase.ACTIONS:
                return ChooseAction(ActionIntent.ATTACK)
            if view.interaction_phase is InteractionPhase.REGULAR_MOVES:
                return ChooseMove(next(self.moves))
            if view.interaction_phase is InteractionPhase.TARGETS:
                return ChooseTarget("enemy_1")
            raise AssertionError(f"unexpected Joruun phase: {view.interaction_phase}")

    battle = Battle(
        player,
        (first, second),
        ui=JoruunMechanicUI(),
        resolver=CombatResolver(rng=rng),
        rng=rng,
    )

    assert battle.player_action() is True
    assert battle.player_action() is True
    assert battle.player_action() is True
    assert not battle.combat_state.conductive_active(player, first)
    assert not battle.combat_state.turbulence_active(player, first)
    assert not battle.combat_state.conductive_active(player, second)
    assert not battle.combat_state.turbulence_active(player, second)
    assert any(
        outcome.outcome_type.value == "lightning_storm_triggered"
        for entry in battle.presentation_session.entries
        for outcome in entry.outcomes
    )


@pytest.mark.parametrize("character_type", (Brawler, BlackMage, RogueArcher, Monk))
def test_real_battle_universal_heal_is_available_to_every_drifter(character_type):
    player = PlayerState(character_type())
    player.health.take_damage(10)
    battle = Battle(
        player,
        create_enemy_state("goblin"),
        ui=ScriptedBattleUI(ChooseAction(ActionIntent.HEAL)),
        resolver=CombatResolver(rng=SequenceRng(10)),
        rng=SequenceRng(1),
    )
    before = player.health.current

    assert battle.player_action() is True
    assert player.health.current > before
    assert battle.combat_state.heal_cooldown_remaining(player) == 3


def test_real_battle_universal_rejection_matrix_preserves_turns_and_logs():
    player = PlayerState(Brawler())
    player.mana_resource.spend(player.mana_resource.current)
    battle = Battle(
        player,
        create_enemy_state("goblin"),
        ui=ScriptedBattleUI(
            ChooseAction(ActionIntent.ATTACK),
            ChooseMove("not an authored move"),
            ChooseAction(ActionIntent.ATTACK),
            ChooseMove("Crestgrave Reaping"),
        ),
        resolver=CombatResolver(rng=SequenceRng(100)),
        rng=SequenceRng(1),
    )
    battle.presentation_session.record(
        BattleLogEntry(
            event_type=BattleEventType.DAMAGE,
            actor_name="previous turn",
            action_name="stale action",
        )
    )

    assert battle.player_action() is True
    assert battle.combat_state.turn_count == 1
    assert any(
        any(
            entry.event_type == BattleEventType.INPUT_REJECTED
            for entry in view.log_entries
        )
        for view in battle.ui.views
    )
    assert any(
        entry.event_type == BattleEventType.MISS
        for entry in battle.presentation_session.entries
    )
    assert all(
        entry.actor_name != "previous turn"
        for entry in battle.presentation_session.entries
    )

    insufficient_mana = PlayerState(BlackMage())
    insufficient_mana.mana_resource.spend(insufficient_mana.mana_resource.current)
    mana_battle = Battle(
        insufficient_mana,
        create_enemy_state("goblin"),
        ui=ScriptedBattleUI(
            ChooseAction(ActionIntent.ATTACK),
            ChooseMove("Gloamweight Sepulcher"),
            GoBack(),
            ChooseAction(ActionIntent.DEFEND),
        ),
        resolver=CombatResolver(rng=SequenceRng(1)),
        rng=SequenceRng(1),
    )
    assert mana_battle.player_action() is True
    assert insufficient_mana.mana_resource.current == 0
    assert mana_battle.combat_state.turn_count == 1

    super_player = PlayerState(Brawler())
    super_before = super_player.super_resource.current
    super_battle = Battle(
        super_player,
        create_enemy_state("goblin"),
        ui=ScriptedBattleUI(
            ChooseAction(ActionIntent.SUPER),
            ChooseAction(ActionIntent.DEFEND),
        ),
        resolver=CombatResolver(rng=SequenceRng(1)),
        rng=SequenceRng(1),
    )
    assert super_battle.player_action() is True
    assert super_player.super_resource.current == super_before
    assert super_battle.combat_state.turn_count == 1


def test_real_enemy_phase_skips_dead_enemy_and_simultaneous_death_is_defeat():
    player = PlayerState(Brawler())
    first, second = create_enemy_state("goblin"), create_enemy_state("goblin")
    first.health.take_damage(first.health.current)
    rng = SequenceRng(1)
    resolver = RecordingCombatResolver(rng=rng)
    battle = Battle(
        player,
        (first, second),
        ui=ScriptedBattleUI(),
        resolver=resolver,
        rng=rng,
    )

    battle.enemy_phase()
    assert tuple(call[0] for call in resolver.calls) == (second,)
    assert second.is_alive()

    class SimultaneousDeathResolver:
        def resolve_move(self, actor, target, move_name, **kwargs):
            del kwargs
            actor.health.take_damage(actor.health.current)
            target.health.take_damage(target.health.current)
            return MoveResult(
                accepted=True,
                hit=True,
                move_name=move_name,
                resource_spent=0,
                damage=target.health.maximum,
                healing=0,
                statuses_applied=(),
                reason=None,
            )

    simultaneous_player = PlayerState(Brawler())
    simultaneous_enemy = create_enemy_state("goblin")
    simultaneous_battle = Battle(
        simultaneous_player,
        simultaneous_enemy,
        ui=ScriptedBattleUI(
            ChooseAction(ActionIntent.ATTACK),
            ChooseMove("Crestgrave Reaping"),
        ),
        resolver=SimultaneousDeathResolver(),
        rng=SequenceRng(1),
    )
    assert simultaneous_battle.run() == "enemy"
    assert simultaneous_battle.interaction_phase is InteractionPhase.COMPLETE


def test_terminal_battle_renders_ordinary_pair_and_boss_without_raw_ids():
    cases = (
        ("Goblin Ambush", ("goblin",)),
        ("Goblin Pair", ("goblin", "goblin")),
        ("Goblin Lord", ("goblin_lord", "goblin", "goblin_warrior")),
    )
    for encounter_label, archetype_ids in cases:
        battle = Battle(
            PlayerState(Brawler()),
            tuple(create_enemy_state(archetype_id) for archetype_id in archetype_ids),
            ui=ScriptedBattleUI(),
            resolver=CombatResolver(rng=SequenceRng(1)),
            rng=SequenceRng(1),
            encounter_label=encounter_label,
        )
        view = battle._build_view()
        for width in (50, 80, 120):
            output = []
            TerminalBattleUI(
                output_func=output.append,
                width_provider=lambda width=width: width,
                unicode_enabled=False,
                ansi_enabled=False,
                interactive=False,
            ).render(view)
            rendered = "\n".join(output)
            assert encounter_label in rendered
            assert all(f"enemy_{index}" not in rendered for index in range(1, 5))
            assert all(len(line) <= width for line in output)
        assert all(enemy.display_label for enemy in view.enemies)

    for enemy in battle.enemies:
        enemy.health.take_damage(enemy.health.current)
    battle.interaction_phase = InteractionPhase.COMPLETE
    final_output = []
    TerminalBattleUI(
        output_func=final_output.append,
        width_provider=lambda: 80,
        unicode_enabled=False,
        ansi_enabled=False,
        interactive=False,
    ).render(battle._build_view())
    final_rendered = "\n".join(final_output)
    assert "Defeated" in final_rendered
    assert "[A] Attack" not in final_rendered
    assert all(f"enemy_{index}" not in final_rendered for index in range(1, 5))

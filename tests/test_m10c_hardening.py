import pytest

from app.combat.battle import Battle
from app.combat.combat_state import CombatState
from app.combat.resolver import CombatResolver
from app.combat.result import CombatOutcomeType
from app.enemies.goblin.definition import Goblin
from app.enemies.factory import create_enemy_state
from app.enemies.state import EnemyState
from app.game.encounter_manifest import create_route_encounter_enemies
from app.game.game_state import GameState
from app.game.overworld_session import OverworldSession, OverworldSessionResult
from app.game.overworld_state import ContextualRoutePhase
from app.player.character import BlackMage, Brawler, Monk, RogueArcher
from app.player.inventory_action import InventoryActionResolver
from app.player.player_state import PlayerState
from app.presentation.battle_models import ActionIntent, InteractionPhase
from app.ui.battle_ui import ChooseAction, ChooseMove, ChooseTarget
from app.ui.terminal_battle_ui import TerminalBattleUI
from app.ui.terminal_overworld_ui import TerminalOverworldUI


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


class RecordingCombatResolver(CombatResolver):
    def __init__(self, *, rng):
        super().__init__(rng=rng)
        self.calls = []
        self.player = None
        self.enemies = ()
        self.other_enemy = None
        self.first_player_target_hp = None
        self.first_player_other_hp = None
        self.player_snapshots = []

    def resolve_move(self, actor, target, move_name, **kwargs):
        result = super().resolve_move(actor, target, move_name, **kwargs)
        self.calls.append((actor, target, move_name, result))
        if actor is self.player:
            self.player_snapshots.append(
                (target, tuple(enemy.health.current for enemy in self.enemies))
            )
        if (
            len(self.calls) == 1
            and actor is self.player
        ):
            self.first_player_target_hp = target.health.current
            self.first_player_other_hp = self.other_enemy.health.current
        return result


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


def test_real_terminal_pair_route_completes_with_ordered_enemy_phase_and_auto_target():
    player = PlayerState(Brawler(), gold=23)
    player.exp_state.gain(41)
    game = GameState(player)
    game.overworld_state.advance_to(
        "surface_goblin_pair",
        contextual_phase=ContextualRoutePhase.ENTER_ENCOUNTER,
    )
    player_identity = player
    before_exp = player.exp_state.current
    before_level = player.level_state.current
    before_gold = player.gold
    overworld_output = []
    battle_output = []
    overworld_inputs = iter(("e", "o", "q", "y"))
    battle_inputs = iter(
        (
            "a",
            "crestgrave reaping",
            "2",
            "a",
            "ironwake dismemberment",
            "1",
            "a",
            "ironwake dismemberment",
        )
    )
    created = {}
    enemy_count = 0

    class RecordingTerminalBattleUI(TerminalBattleUI):
        def __init__(self):
            super().__init__(
                input_func=lambda _prompt: next(battle_inputs),
                output_func=battle_output.append,
                width_provider=lambda: 100,
                unicode_enabled=False,
                ansi_enabled=False,
                interactive=False,
            )
            self.views = []

        def render(self, view):
            self.views.append(view)
            super().render(view)

    def enemy_factory(archetype_id, *, tier):
        nonlocal enemy_count
        enemy = create_enemy_state(archetype_id, tier=tier)
        if enemy_count == 0:
            enemy.health.current = 1
        else:
            enemy.health.current = 20
        enemy_count += 1
        return enemy

    def battle_factory(acting_player, enemies, *, ui):
        rng = AlwaysOneRng()
        resolver = RecordingCombatResolver(rng=rng)
        resolver.player = acting_player
        resolver.enemies = tuple(enemies)
        resolver.other_enemy = resolver.enemies[0]
        battle = Battle(
            acting_player,
            enemies,
            ui=ui,
            resolver=resolver,
            rng=rng,
        )
        created["battle"] = battle
        created["resolver"] = resolver
        return battle

    overworld_ui = TerminalOverworldUI(
        input_func=lambda _prompt: next(overworld_inputs),
        output_func=overworld_output.append,
        width_provider=lambda: 100,
        unicode_enabled=False,
        ansi_enabled=False,
        interactive=False,
    )

    def battle_ui_factory():
        return RecordingTerminalBattleUI()

    result = OverworldSession(
        game,
        ui=overworld_ui,
        battle_factory=battle_factory,
        enemy_factory=enemy_factory,
        battle_ui_factory=battle_ui_factory,
    ).run()

    battle = created["battle"]
    resolver = created["resolver"]
    battle_ui = battle.ui
    first, second = battle.enemies
    assert result is OverworldSessionResult.QUIT
    assert player_identity is battle.player_state is player
    assert resolver.first_player_target_hp is not None
    assert 0 < resolver.first_player_target_hp < second.health.maximum
    assert resolver.first_player_other_hp == 1
    assert tuple(call[0] for call in resolver.calls[:3]) == (
        player,
        first,
        second,
    )
    assert tuple(call[1] for call in resolver.calls[:3]) == (
        second,
        player,
        player,
    )
    assert tuple(call[0] for call in resolver.calls[3:]) == (
        player,
        second,
        player,
    )
    assert tuple(call[1] for call in resolver.calls[3:]) == (
        first,
        player,
        second,
    )
    assert resolver.player_snapshots[1][0] is first
    assert resolver.player_snapshots[1][1][0] == 0
    assert resolver.player_snapshots[1][1][1] > 0
    assert resolver.player_snapshots[2][0] is second
    assert resolver.player_snapshots[2][1] == (0, 0)
    assert tuple(enemy.display_label for enemy in battle._build_view().enemies) == (
        "Goblin 1",
        "Goblin 2",
    )
    assert "Goblin 1" in "\n".join(battle_output)
    assert "Goblin 2" in "\n".join(battle_output)
    assert sum(
        view.interaction_phase is InteractionPhase.TARGETS
        for view in battle_ui.views
    ) == 2
    final = battle_ui.views[-1]
    assert final.interaction_phase is InteractionPhase.COMPLETE
    assert final.action_options == ()
    assert final.move_options == ()
    assert final.target_options == ()
    assert final.inventory_items == ()
    assert tuple(enemy.temporary_labels for enemy in final.enemies) == (
        ("Defeated",),
        ("Defeated",),
    )
    assert "OVERWORLD  |  Goblin Warrior" in "\n".join(overworld_output)
    assert game.world_state.defeated_encounters == ("surface_goblin_pair",)
    assert game.overworld_state.current_route_node_id == "surface_warrior_solo"
    assert player.exp_state.current == before_exp
    assert player.level_state.current == before_level
    assert player.gold == before_gold


def test_authored_goblin_lord_composition_renders_at_narrow_and_wide_widths():
    enemies = create_route_encounter_enemies("surface_goblin_lord")
    battle = Battle(
        PlayerState(Brawler()),
        enemies,
        ui=ScriptedBattleUI(()),
        resolver=CombatResolver(rng=AlwaysOneRng()),
        rng=AlwaysOneRng(),
    )
    view = battle._build_view()
    expected_labels = ("Goblin Lord", "Goblin", "Goblin Warrior")

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
        assert all(label in rendered for label in expected_labels)
        assert all(len(line) <= width for line in output)
        first_indexes = [
            next(index for index, line in enumerate(output) if label in line)
            for label in expected_labels
        ]
        assert first_indexes == sorted(first_indexes)


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

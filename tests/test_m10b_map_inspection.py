from unittest.mock import patch

import pytest

from app.game.game_state import GameState
from app.game.overworld_route import SURFACE_ROUTE_NODES
from app.player.character import Brawler
from app.player.player_state import PlayerState
from app.presentation.overworld_models import (
    OverworldAction,
    OverworldAvailabilityReason,
    OverworldScreen,
)
from app.presentation.overworld_presenter import OverworldPresenter
from app.ui.terminal_overworld_ui import TerminalOverworldUI


EXPECTED_INSPECTIONS = (
    ("surface_goblin_solo", "Goblin Ambush", ("Goblin",), False),
    ("surface_goblin_pair", "Goblin Pair", ("2 Goblins",), False),
    ("surface_warrior_solo", "Goblin Warrior", ("Goblin Warrior",), False),
    (
        "surface_warrior_pair",
        "Warrior Patrol",
        ("2 Goblin Warriors",),
        False,
    ),
    ("surface_shaman_solo", "Goblin Shaman", ("Goblin Shaman",), False),
    ("surface_shaman_pair", "Shaman Pair", ("2 Goblin Shamans",), False),
    (
        "surface_elite_patrol",
        "Elite Patrol",
        ("Goblin Elite", "Goblin"),
        False,
    ),
    (
        "surface_goblin_lord",
        "Goblin Lord",
        ("Goblin Lord", "Goblin", "Goblin Warrior"),
        True,
    ),
)


def game_at(node_id):
    game = GameState(PlayerState(Brawler()))
    if node_id == SURFACE_ROUTE_NODES[0].node_id:
        return game
    for node in SURFACE_ROUTE_NODES[1:]:
        game.overworld_state.advance_to(node.node_id)
        if node.node_id == node_id:
            return game
    raise AssertionError(f"unknown test route node: {node_id}")


def option(view, action):
    return next(value for value in view.options if value.action is action)


@pytest.mark.parametrize(
    ("node_id", "label", "composition", "boss"),
    EXPECTED_INSPECTIONS,
)
def test_every_combat_node_exposes_exact_authored_inspection(
    node_id,
    label,
    composition,
    boss,
):
    game = game_at(node_id)
    before = game.snapshot()

    route_map = OverworldPresenter().build(game, screen=OverworldScreen.MAP)
    inspection = OverworldPresenter().build(
        game,
        screen=OverworldScreen.MAP_INSPECT,
    )

    assert option(route_map, OverworldAction.INSPECT).enabled is True
    assert inspection.encounter_inspection.encounter_label == label
    assert inspection.encounter_inspection.composition == composition
    assert inspection.encounter_inspection.boss is boss
    assert game.snapshot() == before


@pytest.mark.parametrize(
    ("rest_node_id", "next_label", "composition"),
    (
        (
            "surface_rest_after_warrior_solo",
            "Warrior Patrol",
            ("2 Goblin Warriors",),
        ),
        (
            "surface_rest_after_shaman_pair",
            "Elite Patrol",
            ("Goblin Elite", "Goblin"),
        ),
        (
            "surface_rest_before_goblin_lord",
            "Goblin Lord",
            ("Goblin Lord", "Goblin", "Goblin Warrior"),
        ),
    ),
)
def test_rest_nodes_inspect_the_next_combat_encounter(
    rest_node_id,
    next_label,
    composition,
):
    game = game_at(rest_node_id)
    inspection = OverworldPresenter().build(
        game,
        screen=OverworldScreen.MAP_INSPECT,
    ).encounter_inspection

    assert inspection.encounter_label == next_label
    assert inspection.composition == composition


def test_dungeon_entrance_disables_inspection_and_exposes_no_model():
    game = game_at("surface_dungeon_entrance")
    route_map = OverworldPresenter().build(game, screen=OverworldScreen.MAP)
    inspection = OverworldPresenter().build(
        game,
        screen=OverworldScreen.MAP_INSPECT,
    )
    inspect_option = option(route_map, OverworldAction.INSPECT)

    assert inspect_option.enabled is False
    assert (
        inspect_option.disabled_reason
        is OverworldAvailabilityReason.ENCOUNTER_INSPECTION_UNAVAILABLE
    )
    assert inspection.encounter_inspection is None


def test_inspection_never_creates_enemy_runtime_objects():
    game = game_at("surface_goblin_lord")

    with patch(
        "app.enemies.factory.create_enemy_state",
        side_effect=AssertionError("runtime enemy creation is forbidden"),
    ):
        inspection = OverworldPresenter().build(
            game,
            screen=OverworldScreen.MAP_INSPECT,
        )

    assert inspection.encounter_inspection.composition == (
        "Goblin Lord",
        "Goblin",
        "Goblin Warrior",
    )


def test_terminal_inspection_uses_only_player_facing_authored_labels():
    game = game_at("surface_goblin_lord")
    view = OverworldPresenter().build(
        game,
        screen=OverworldScreen.MAP_INSPECT,
    )
    output = []
    ui = TerminalOverworldUI(
        output_func=output.append,
        width_provider=lambda: 100,
        unicode_enabled=False,
        interactive=False,
    )

    ui.render(view)
    text = "\n".join(output)

    assert "ENCOUNTER INSPECTION" in text
    assert "Boss Encounter" in text
    assert "Goblin Lord" in text
    assert "Goblin Warrior" in text
    assert "surface_" not in text
    assert "goblin_" not in text
    assert "map_inspect" not in text


def test_inspection_rebuilds_are_independent_immutable_and_non_mutating():
    game = game_at("surface_goblin_pair")
    presenter = OverworldPresenter()
    before = game.snapshot()

    first = presenter.build(game, screen=OverworldScreen.MAP_INSPECT)
    second = presenter.build(game, screen=OverworldScreen.MAP_INSPECT)

    assert first == second
    assert first is not second
    assert first.encounter_inspection is not second.encounter_inspection
    assert game.snapshot() == before
    with pytest.raises(AttributeError):
        first.encounter_inspection.encounter_label = "Changed"

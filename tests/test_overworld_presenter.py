import pytest

from app.game.game_state import GameState
from app.game.overworld_route import SECOND_SURFACE_NODE_ID
from app.game.overworld_state import ContextualRoutePhase
from app.player.character import BlackMage, Brawler, Monk, RogueArcher
from app.player.player_state import PlayerState
from app.presentation.overworld_models import (
    MapNodeState,
    OverworldAction,
    OverworldAvailabilityReason,
    OverworldScreen,
)
from app.presentation.overworld_presenter import OverworldPresenter


def create_game(character_type=Brawler):
    return GameState(PlayerState(character_type()))


def option(view, action):
    return next(value for value in view.options if value.action is action)


def test_main_view_uses_authored_labels_and_only_the_valid_contextual_action():
    game = create_game()
    presenter = OverworldPresenter()

    initial = presenter.build(game)
    game.overworld_state.set_contextual_route_phase(ContextualRoutePhase.RETRY)
    retry = presenter.build(game)
    game.overworld_state.advance_to(SECOND_SURFACE_NODE_ID)
    paused = presenter.build(game)

    assert initial.location_label == "Goblin Ambush"
    assert [value.label for value in initial.options] == [
        "Character",
        "Items",
        "Map",
        "Options",
        "Enter Encounter",
    ]
    assert option(retry, OverworldAction.RETRY).enabled is True
    assert not any(
        value.action in {OverworldAction.ENTER_ENCOUNTER, OverworldAction.RETRY}
        for value in paused.options
    )
    assert paused.location_label == "Goblin Pair"
    assert "surface_" not in repr(initial)
    assert "surface_" not in repr(paused)


@pytest.mark.parametrize(
    ("character_type", "weapon_name", "intended_wielder", "move_name"),
    (
        (Brawler, "Sunder-Spire", "Branoc", "Brace"),
        (BlackMage, "Needle of Plain Iron", "Azhvielle", "Mournglass Bloom"),
        (RogueArcher, "Sathren", "Zhaivra", "Infused Barb"),
        (Monk, "Sky-Needle", "Joruun", "Lightning Palm"),
    ),
)
def test_character_skills_and_weapon_views_use_each_drifters_authored_data(
    character_type,
    weapon_name,
    intended_wielder,
    move_name,
):
    game = create_game(character_type)
    presenter = OverworldPresenter()

    character = presenter.build(game, screen=OverworldScreen.CHARACTER)
    skills = presenter.build(game, screen=OverworldScreen.SKILLS)
    weapon = presenter.build(game, screen=OverworldScreen.WEAPON)

    assert len(character.character.stats) == 6
    assert character.character.level == 1
    assert character.character.exp_current == 0
    assert character.character.exp_threshold == 100
    assert skills.skills.growth_points_available is None
    assert all(row.increase_visible for row in skills.skills.stats)
    assert all(not row.increase_enabled for row in skills.skills.stats)
    assert move_name in tuple(move.name for move in skills.skills.moves)
    assert weapon.weapon.name == weapon_name
    assert weapon.weapon.intended_wielder == intended_wielder
    assert weapon.weapon.description


def test_equipment_view_does_not_reinterpret_internal_equipment_slots():
    view = OverworldPresenter().build(
        create_game(),
        screen=OverworldScreen.EQUIPMENT,
    )

    assert view.equipment.necklace.label == "Necklace"
    assert view.equipment.necklace.item_name == "Empty"
    assert view.equipment.ring.label == "Ring"
    assert view.equipment.ring.item_name == "Empty"
    assert view.equipment.benefits == ("None",)
    assert "Off Hand" not in repr(view)
    assert "Body" not in repr(view)


def test_zh_aivra_items_are_selected_and_inspected_without_mutation():
    game = create_game(RogueArcher)
    presenter = OverworldPresenter()
    before = game.snapshot()

    inventory = presenter.build(game, screen=OverworldScreen.ITEMS)
    ember = next(item for item in inventory.inventory.items if item.display_name == "Ember Shard")
    selected = presenter.build(
        game,
        screen=OverworldScreen.ITEMS,
        selected_item_key=ember.selection_key,
    )
    inspected = presenter.build(
        game,
        screen=OverworldScreen.ITEM_INSPECT,
        selected_item_key=ember.selection_key,
    )

    assert [item.display_name for item in inventory.inventory.items] == [
        "Ember Shard",
        "Deep Coal",
        "Night Berry",
    ]
    assert option(inventory, OverworldAction.INSPECT).enabled is False
    assert option(selected, OverworldAction.INSPECT).enabled is True
    assert option(selected, OverworldAction.USE).enabled is False
    assert (
        option(selected, OverworldAction.USE).disabled_reason
        is OverworldAvailabilityReason.NO_OVERWORLD_USE
    )
    assert inspected.inventory.inspected_item.description.startswith("A heat-bearing")
    assert game.snapshot() == before


def test_empty_inventory_and_disabled_item_actions_are_explicit():
    view = OverworldPresenter().build(
        create_game(),
        screen=OverworldScreen.ITEMS,
    )

    assert view.inventory.items == ()
    assert option(view, OverworldAction.CRAFT).enabled is False
    assert option(view, OverworldAction.INSPECT).enabled is False
    assert option(view, OverworldAction.USE).enabled is False
    assert option(view, OverworldAction.BACK).enabled is True


def test_map_is_complete_read_only_and_marks_exact_current_and_completed_nodes():
    game = create_game()
    game.world_state.mark_encounter_defeated("surface_goblin_solo")
    game.overworld_state.advance_to(SECOND_SURFACE_NODE_ID)

    view = OverworldPresenter().build(game, screen=OverworldScreen.MAP)

    assert len(view.route_map.nodes) == 12
    assert view.route_map.nodes[0].state is MapNodeState.COMPLETED
    assert view.route_map.nodes[1].state is MapNodeState.CURRENT
    assert sum(node.kind_label == "Rest" for node in view.route_map.nodes) == 3
    assert view.route_map.nodes[-2].kind_label == "Boss"
    assert view.route_map.nodes[-1].kind_label == "Dungeon"
    assert option(view, OverworldAction.INSPECT).enabled is False
    assert "surface_" not in repr(view)


def test_options_and_quit_confirmation_follow_the_approved_hierarchy():
    presenter = OverworldPresenter()
    game = create_game()

    options = presenter.build(game, screen=OverworldScreen.OPTIONS)
    confirmation = presenter.build(
        game,
        screen=OverworldScreen.QUIT_CONFIRMATION,
    )

    assert [value.label for value in options.options] == [
        "Save",
        "Quit",
        "Load",
        "Back",
    ]
    assert option(options, OverworldAction.SAVE).enabled is False
    assert option(options, OverworldAction.LOAD).enabled is False
    assert option(options, OverworldAction.QUIT).enabled is True
    assert [value.action for value in confirmation.options] == [
        OverworldAction.CONFIRM,
        OverworldAction.CANCEL,
    ]


def test_presenter_rebuilds_are_pure_and_return_independent_immutable_views():
    game = create_game(RogueArcher)
    presenter = OverworldPresenter()
    before = game.snapshot()

    first = presenter.build(game, screen=OverworldScreen.ITEMS)
    second = presenter.build(game, screen=OverworldScreen.ITEMS)

    assert first == second
    assert first is not second
    assert first.inventory is not second.inventory
    assert game.snapshot() == before
    with pytest.raises(AttributeError):
        first.location_label = "Changed"

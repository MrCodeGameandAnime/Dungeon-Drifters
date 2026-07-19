import pytest

from app.game.game_state import GameState
from app.game.overworld_route import SECOND_SURFACE_NODE_ID
from app.game.overworld_state import ContextualRoutePhase
from app.player.character import Brawler, RogueArcher
from app.player.player_state import PlayerState
from app.player.run_items import owned_run_item_definitions
from app.presentation.overworld_models import (
    MapNodeState,
    OverworldAction,
    OverworldAvailabilityReason,
    OverworldScreen,
)
from app.presentation.overworld_presenter import OverworldPresenter, STAT_ORDER
from app.world.character_profiles.roster import get_character_profiles


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
    ]
    assert (
        initial.contextual_route_option.action
        is OverworldAction.ENTER_ENCOUNTER
    )
    assert retry.options == initial.options
    assert paused.options == initial.options
    assert retry.contextual_route_option.action is OverworldAction.RETRY
    assert paused.contextual_route_option is None
    assert paused.location_label == "Goblin Pair"
    assert "surface_" not in repr(initial)
    assert "surface_" not in repr(paused)


@pytest.mark.parametrize("profile", get_character_profiles())
def test_all_drifter_views_expose_complete_authored_data_without_mutation(
    profile,
):
    player = PlayerState(profile.create_character())
    player.health.take_damage(7)
    assert player.mana_resource.spend(3) is True
    player.super_resource.gain(29)
    signature_weapon = player.get_equipped("weapon")
    player.inventory.add_item(signature_weapon)
    game = GameState(player)
    presenter = OverworldPresenter()
    before = game.snapshot()

    character = presenter.build(game, screen=OverworldScreen.CHARACTER)
    skills = presenter.build(game, screen=OverworldScreen.SKILLS)
    weapon = presenter.build(game, screen=OverworldScreen.WEAPON)
    inventory = presenter.build(game, screen=OverworldScreen.ITEMS)

    assert tuple(row.label for row in character.character.stats) == (
        "Strength",
        "Constitution",
        "Intelligence",
        "Spirit",
        "Dexterity",
        "Intuition",
    )
    permanent_stats = player.character.permanent_stats.as_dict()
    assert tuple(row.value for row in character.character.stats) == tuple(
        permanent_stats[name] for name, _ in STAT_ORDER
    )
    assert character.character.display_name == player.character.full_display_name
    assert character.character.archetype_label == player.character.archetype_name
    assert character.character.hp_current == player.health.current
    assert character.character.hp_maximum == player.health.maximum
    assert character.character.mana_current == player.mana_resource.current
    assert character.character.mana_maximum == player.mana_resource.maximum
    assert character.character.super_current == player.super_resource.current
    assert character.character.super_maximum == player.super_resource.maximum

    assert character.character.level == 1
    assert character.character.exp_current == 0
    assert character.character.exp_threshold == 100
    assert skills.skills.growth_points_available is None
    assert all(row.increase_visible for row in skills.skills.stats)
    assert all(not row.increase_enabled for row in skills.skills.stats)
    assert tuple(
        (move.name, move.description) for move in skills.skills.moves
    ) == tuple(
        (move.name, move.description) for move in player.combat_moves
    )

    assert weapon.weapon.name == signature_weapon.name
    assert weapon.weapon.weapon_type == signature_weapon.weapon_type
    assert weapon.weapon.intended_wielder == signature_weapon.intended_wielder
    assert tuple(
        (bonus.label, bonus.amount) for bonus in weapon.weapon.bonuses
    ) == tuple(
        (label, signature_weapon.stat_bonuses[name])
        for name, label in STAT_ORDER
        if name in signature_weapon.stat_bonuses
    )
    assert weapon.weapon.description == signature_weapon.description

    expected_items = [
        (signature_weapon.name, 1, signature_weapon.description),
    ]
    expected_items.extend(
        (
            definition.display_name,
            player.character_run_state.item_quantity(definition.item_id),
            definition.description,
        )
        for definition in owned_run_item_definitions(
            player.character_run_state
        )
    )
    assert tuple(
        (item.display_name, item.quantity, item.description)
        for item in inventory.inventory.items
    ) == tuple(expected_items)

    assert game.snapshot() == before
    with pytest.raises(AttributeError):
        character.character.super_current = 0


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


def test_map_uses_overworld_state_as_the_rest_completion_owner():
    game = create_game()
    game.overworld_state.record_resolved_rest_node(
        "surface_rest_after_warrior_solo"
    )
    game.world_state.mark_encounter_defeated(
        "surface_rest_after_shaman_pair"
    )

    view = OverworldPresenter().build(game, screen=OverworldScreen.MAP)
    states = {
        node.display_label: node.state for node in view.route_map.nodes
    }

    assert states["Woodland Rest"] is MapNodeState.COMPLETED
    assert states["Ritual Clearing Rest"] is MapNodeState.REMAINING
    assert states["Final Approach Rest"] is MapNodeState.REMAINING
    assert "surface_rest" not in " ".join(states)


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


@pytest.mark.parametrize(
    ("screen", "populated_field"),
    (
        (OverworldScreen.MAIN, None),
        (OverworldScreen.CHARACTER, "character"),
        (OverworldScreen.SKILLS, "skills"),
        (OverworldScreen.WEAPON, "weapon"),
        (OverworldScreen.EQUIPMENT, "equipment"),
        (OverworldScreen.ITEMS, "inventory"),
        (OverworldScreen.ITEM_INSPECT, "inventory"),
        (OverworldScreen.MAP, "route_map"),
        (OverworldScreen.OPTIONS, None),
        (OverworldScreen.QUIT_CONFIRMATION, None),
    ),
)
def test_each_screen_exposes_only_its_approved_screen_specific_model(
    screen,
    populated_field,
):
    game = create_game(RogueArcher)
    selected_key = None
    if screen is OverworldScreen.ITEM_INSPECT:
        items_view = OverworldPresenter().build(
            game,
            screen=OverworldScreen.ITEMS,
        )
        selected_key = items_view.inventory.items[0].selection_key

    view = OverworldPresenter().build(
        game,
        screen=screen,
        selected_item_key=selected_key,
    )
    fields = (
        "character",
        "skills",
        "weapon",
        "equipment",
        "inventory",
        "route_map",
    )

    assert tuple(
        field for field in fields if getattr(view, field) is not None
    ) == (() if populated_field is None else (populated_field,))


def test_all_deferred_and_illegal_presentation_controls_remain_disabled():
    presenter = OverworldPresenter()
    game = create_game(RogueArcher)
    skills = presenter.build(game, screen=OverworldScreen.SKILLS)
    items = presenter.build(game, screen=OverworldScreen.ITEMS)
    selected = presenter.build(
        game,
        screen=OverworldScreen.ITEMS,
        selected_item_key=items.inventory.items[0].selection_key,
    )
    route_map = presenter.build(game, screen=OverworldScreen.MAP)
    options = presenter.build(game, screen=OverworldScreen.OPTIONS)

    assert all(not row.increase_enabled for row in skills.skills.stats)
    assert option(items, OverworldAction.CRAFT).enabled is False
    assert option(selected, OverworldAction.USE).enabled is False
    assert option(route_map, OverworldAction.INSPECT).enabled is False
    assert option(options, OverworldAction.SAVE).enabled is False
    assert option(options, OverworldAction.LOAD).enabled is False

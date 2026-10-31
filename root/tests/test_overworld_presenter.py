import pytest

from app.content.catalog import get_drifter_spec
from app.game.game_state import GameState
from tests.content_test_support import SECOND_SURFACE_NODE_ID
from app.game.overworld_state import ContextualRoutePhase
from app.player.player_state import PlayerState
from app.player.progression import MAXIMUM_LEVEL
from app.player.run_items import owned_run_item_definitions
from app.presentation.overworld_models import (
    MapNodeState,
    OverworldAction,
    OverworldAvailabilityReason,
    OverworldScreen,
)
from app.presentation.overworld_presenter import OverworldPresenter, STAT_ORDER
from app.content.catalog import DRIFTER_SPECS, get_weapon_spec
from tests.game_test_support import (
    advance_surface_to,
    completed_hub_game,
    recruited_pair_game,
    hub_game,
)


def test_map_completion_uses_world_for_combat_and_overworld_for_rest():
    route_map = OverworldPresenter().build(
        hub_game(), screen=OverworldScreen.MAP,
    ).route_map

    assert tuple(node.state for node in route_map.nodes[:-1]) == (
        MapNodeState.COMPLETED,
    ) * 11
    assert route_map.nodes[-1].state is MapNodeState.CURRENT


def get_character_profiles():
    return DRIFTER_SPECS


def create_game(drifter_id="branoc"):
    return GameState(PlayerState(get_drifter_spec(drifter_id).create_character()))


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
    game.overworld_state.advance_to(
        "surface_warrior_solo",
        contextual_phase=ContextualRoutePhase.ENTER_ENCOUNTER,
    )
    game.overworld_state.advance_to("surface_rest_after_warrior_solo")
    rest_main = presenter.build(game)
    rest_screen = presenter.build(game, screen=OverworldScreen.REST)

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
    assert rest_main.contextual_route_option.action is OverworldAction.REST
    assert rest_screen.contextual_route_option.action is OverworldAction.SKIP_REST
    assert [option.label for option in rest_screen.options] == [
        "Rest",
        "Save",
        "Quit",
        "Menu",
    ]
    assert rest_screen.options[1].enabled is False
    assert "surface_" not in repr(initial)
    assert "surface_" not in repr(paused)


def test_hub_location_label_is_preserved_in_secondary_menus():
    game = create_game()
    assert game.party_state.arrive_at_hub(game.player_state)
    presenter = OverworldPresenter()

    views = tuple(
        presenter.build(game, screen=screen)
        for screen in (
            OverworldScreen.CHARACTER,
            OverworldScreen.ITEMS,
            OverworldScreen.MAP,
            OverworldScreen.OPTIONS,
        )
    )

    assert tuple(view.location_label for view in views) == (
        "Floor 1 Hub",
        "Floor 1 Hub",
        "Floor 1 Hub",
        "Floor 1 Hub",
    )


def test_merchant_view_exposes_storage_pack_and_authored_alchemy_recipes():
    game = completed_hub_game()
    game.party_state.add_shared_items({"healing_potion": 2, "goblin_scrap": 1})
    assert game.party_state.load_carried_supplies({"healing_potion": 1})

    view = OverworldPresenter().build(game, screen=OverworldScreen.MERCHANT)

    assert view.hub_economy.shared_gold == game.party_state.shared_gold
    assert view.hub_economy.carried_units == 1
    potion = next(
        item for item in view.hub_economy.items
        if item.item_id == "healing_potion"
    )
    assert (potion.stored_quantity, potion.carried_quantity) == (1, 1)
    assert potion.can_buy and potion.can_sell and potion.can_load and potion.can_unload
    recipe = next(
        recipe for recipe in view.hub_economy.recipes
        if recipe.recipe_id == "healing_potion"
    )
    assert recipe.can_craft is False
    assert recipe.ingredient_summary == ("Medicinal Herb x1", "Clean Water x1")
    assert recipe.output_summary == ("Healing Potion x1",)


def test_items_separate_carried_supplies_from_storage_and_only_pack_is_usable():
    game = completed_hub_game()
    game.party_state.add_shared_items({"healing_potion": 2})
    assert game.party_state.load_carried_supplies({"healing_potion": 1})
    game.member_for_drifter_id("azhvielle").health.take_damage(30)
    presenter = OverworldPresenter()

    items = presenter.build(game, screen=OverworldScreen.ITEMS)
    potions = tuple(
        item for item in items.inventory.items
        if item.display_name == "Healing Potion"
    )
    selected_pack = presenter.build(
        game,
        screen=OverworldScreen.ITEMS,
        selected_item_key="carried-item:healing_potion",
    )

    assert [(item.quantity, item.location_label) for item in potions] == [
        (1, "Hub Storage"),
        (1, "Carried Pack"),
    ]
    assert tuple(
        item.location_label for item in potions if item.overworld_use_enabled
    ) == ("Carried Pack",)
    assert option(selected_pack, OverworldAction.USE).enabled


def test_two_member_completed_hub_offers_both_ordered_party_choices():
    game = completed_hub_game()
    presenter = OverworldPresenter()

    hub = presenter.build(game, screen=OverworldScreen.HUB)
    selection = presenter.build(game, screen=OverworldScreen.PARTY_SELECTION)

    assert option(hub, OverworldAction.SELECT_PARTY).enabled is True
    assert tuple(choice.drifter_ids for choice in selection.active_party_choices) == (
        ("branoc", "azhvielle"),
        ("azhvielle", "branoc"),
    )


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
    assert skills.skills.growth_points_available == 0
    assert skills.skills.growth_message == "Earn Growth Points by leveling up."
    assert tuple(row.stat_name for row in skills.skills.stats) == tuple(
        name for name, _ in STAT_ORDER
    )
    assert all(row.increase_visible for row in skills.skills.stats)
    assert all(not row.increase_enabled for row in skills.skills.stats)
    assert all(
        row.disabled_reason is OverworldAvailabilityReason.NO_GROWTH_POINTS
        for row in skills.skills.stats
    )
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
    assert len(weapon.weapon.components) == 4
    assert tuple(
        component.installed_component_id
        for component in weapon.weapon.components
    ) == tuple(
        slot.starting_component_id
        for slot in get_weapon_spec(signature_weapon.item_id).progression.slots
    )
    assert weapon.weapon.physical_identity is None
    assert weapon.weapon.mystical_identity is None

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


def test_weapon_view_shows_installed_parts_and_merchant_offers_uninstalled_recipes():
    player = PlayerState(get_drifter_spec("branoc").create_character())
    game = GameState(player)
    assert game.party_state.arrive_at_hub(player)
    game.party_state.add_shared_items({"grade_i_metal": 1})
    presenter = OverworldPresenter()

    weapon = presenter.build(game, screen=OverworldScreen.WEAPON).weapon
    grip = next(slot for slot in weapon.components if slot.slot_id == "grip_binding")
    assert grip.installed_component_id == "sunder_spire_grip"

    merchant = presenter.build(game, screen=OverworldScreen.MERCHANT).merchant
    blade_recipe = next(
        recipe
        for recipe in merchant.component_recipes
        if recipe.component_id == "sunder_spire_blade_reinforced"
    )
    assert blade_recipe.material_name == "Scrap metal"
    assert blade_recipe.material_cost == 1
    assert blade_recipe.can_craft is True
    assert blade_recipe.effect_summary == (
        "Crestgrave Reaping: Power +2, Accuracy -2",
        "Heavy identity +1",
    )


def test_merchant_tier_v_offer_reports_cost_chance_and_requirements():
    player = PlayerState(get_drifter_spec("branoc").create_character())
    game = GameState(player)
    assert game.party_state.arrive_at_hub(player)
    game.party_state.add_crafting_experience(990)
    for slot_id in player.signature_weapon_state.slot_progress:
        player.signature_weapon_state.set_slot_progress(slot_id, 100)
    costs = {
        "grade_iv_metal": 12,
        "grade_iv_fiber": 12,
        "grade_iv_timber": 12,
        "grade_iv_cores": 12,
    }
    game.party_state.add_shared_items(costs)

    merchant = OverworldPresenter().build(
        game,
        screen=OverworldScreen.MERCHANT,
    ).merchant

    assert merchant.tier_v.can_attempt is True
    assert merchant.tier_v.completed is False
    assert merchant.tier_v.success_chance_percent == 20
    assert {
        material.item_id: (material.available, material.required)
        for material in merchant.tier_v.materials
    } == {item_id: (quantity, quantity) for item_id, quantity in costs.items()}


def test_installed_component_recipe_is_hidden_for_that_drifter():
    player = PlayerState(get_drifter_spec("branoc").create_character())
    game = GameState(player)
    assert game.party_state.arrive_at_hub(player)
    installed_id = "sunder_spire_grip_braided"
    player.signature_weapon_state.install_component("grip_binding", installed_id)
    merchant = OverworldPresenter().build(
        game,
        screen=OverworldScreen.MERCHANT,
    ).merchant

    assert installed_id not in {
        recipe.component_id for recipe in merchant.component_recipes
    }


def test_component_recipe_visibility_is_independent_for_each_drifter():
    game = recruited_pair_game()
    lead = game.player_state
    lead.signature_weapon_state.install_component(
        "blade_guard",
        "sunder_spire_blade_reinforced",
    )
    game.party_state.add_shared_items({"grade_i_metal": 1})

    companion_merchant = OverworldPresenter().build(
        game,
        screen=OverworldScreen.MERCHANT,
        selected_merchant_target_id="azhvielle",
    ).merchant

    assert companion_merchant.selected_target_id == "azhvielle"
    assert "needle_focus_fitted" in {
        recipe.component_id for recipe in companion_merchant.component_recipes
    }


def test_weapon_component_view_explains_its_combat_and_identity_effects():
    player = PlayerState(get_drifter_spec("branoc").create_character())
    game = GameState(player)
    assert game.party_state.arrive_at_hub(player)
    player.signature_weapon_state.install_component(
        "blade_guard",
        "sunder_spire_blade_reinforced",
    )

    weapon = OverworldPresenter().build(
        game,
        screen=OverworldScreen.WEAPON,
    ).weapon
    blade = next(slot for slot in weapon.components if slot.slot_id == "blade_guard")

    assert blade.installed_component_id == "sunder_spire_blade_reinforced"
    assert blade.installed_effect_summary == (
        "Crestgrave Reaping: Power +2, Accuracy -2",
        "Heavy identity +1",
    )


def test_skills_view_reports_effective_move_values_after_component_install():
    player = PlayerState(get_drifter_spec("branoc").create_character())
    player.signature_weapon_state.install_component(
        "blade_guard",
        "sunder_spire_blade_reinforced",
    )
    game = GameState(player)

    skills = OverworldPresenter().build(
        game,
        screen=OverworldScreen.SKILLS,
    ).skills
    move = next(
        move for move in skills.moves if move.name == "Crestgrave Reaping"
    )

    assert move.power == 11
    assert move.accuracy == 90


def test_items_view_includes_shared_dropped_and_crafting_items():
    game = create_game()
    game.party_state.add_shared_items({"goblin_scrap": 3, "grade_i_metal": 1})

    inventory = OverworldPresenter().build(
        game,
        screen=OverworldScreen.ITEMS,
    ).inventory

    assert tuple(
        (item.selection_key, item.display_name, item.quantity)
        for item in inventory.items
        if item.selection_key.startswith("shared-item:")
    ) == (
        ("shared-item:goblin_scrap", "Goblin Scrap", 3),
        ("shared-item:grade_i_metal", "Scrap metal", 1),
    )


def test_character_progression_presents_zero_and_partial_exp_without_mutation():
    game = create_game()
    presenter = OverworldPresenter()

    zero = presenter.build(game, screen=OverworldScreen.CHARACTER).character
    game.player_state.exp_state.current = 40
    partial = presenter.build(game, screen=OverworldScreen.CHARACTER).character

    assert zero.exp_current == 0
    assert zero.exp_threshold == 100
    assert zero.exp_fill_bps == 0
    assert partial.exp_current == 40
    assert partial.exp_threshold == 100
    assert partial.exp_fill_bps == 4_000


def test_character_progression_presents_level_cap_without_dividing_by_none():
    game = create_game()
    game.player_state.level_state.current = MAXIMUM_LEVEL
    game.player_state.exp_state.current = 0

    view = OverworldPresenter().build(
        game,
        screen=OverworldScreen.CHARACTER,
    ).character

    assert view.level == MAXIMUM_LEVEL
    assert view.exp_current == 0
    assert view.exp_threshold is None
    assert view.exp_fill_bps == 10_000


def test_skills_present_live_growth_points_and_stat_availability():
    game = create_game()
    player = game.player_state
    player.gain_experience(100)
    player.character.permanent_stats.set_stat("constitution", 100)
    weapon_bonus = player.get_equipped("weapon").stat_bonuses.get("strength", 0)

    view = OverworldPresenter().build(
        game,
        screen=OverworldScreen.SKILLS,
    ).skills

    assert view.growth_points_available == 3
    assert view.growth_message == (
        "Spend 1 Growth Point to increase one permanent stat by 1."
    )
    assert all(
        row.increase_enabled
        for row in view.stats
        if row.stat_name != "constitution"
    )
    constitution = next(row for row in view.stats if row.stat_name == "constitution")
    strength = next(row for row in view.stats if row.stat_name == "strength")
    assert constitution.disabled_reason is OverworldAvailabilityReason.STAT_AT_MAXIMUM
    assert not constitution.increase_enabled
    assert strength.value == player.character.permanent_stats.strength
    assert strength.value != player.effective_stat("strength")
    assert player.effective_stat("strength") == strength.value + weapon_bonus


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
    game = create_game("zhaivra")
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
    assert option(view, OverworldAction.INSPECT).enabled is True
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


@pytest.mark.parametrize(
    ("rest_node_id", "rest_label", "successor_id", "successor_label"),
    (
        (
            "surface_rest_after_warrior_solo",
            "Woodland Rest",
            "surface_warrior_pair",
            "Warrior Patrol",
        ),
        (
            "surface_rest_after_shaman_pair",
            "Ritual Clearing Rest",
            "surface_elite_patrol",
            "Elite Patrol",
        ),
        (
            "surface_rest_before_goblin_lord",
            "Final Approach Rest",
            "surface_goblin_lord",
            "Goblin Lord",
        ),
    ),
    ids=("woodland", "ritual_clearing", "final_approach"),
)
def test_map_marks_each_rest_completed_only_after_resolution(
    rest_node_id,
    rest_label,
    successor_id,
    successor_label,
):
    game = create_game()
    advance_surface_to(game, rest_node_id)

    before = OverworldPresenter().build(game, screen=OverworldScreen.MAP)
    before_states = {
        node.display_label: node.state for node in before.route_map.nodes
    }
    assert before_states[rest_label] is MapNodeState.CURRENT

    game.overworld_state.record_resolved_rest_node(rest_node_id)
    game.overworld_state.advance_to(successor_id)
    after = OverworldPresenter().build(game, screen=OverworldScreen.MAP)
    after_states = {
        node.display_label: node.state for node in after.route_map.nodes
    }

    assert after_states[rest_label] is MapNodeState.COMPLETED
    assert after_states[successor_label] is MapNodeState.CURRENT
    assert "surface_" not in repr(before)
    assert "surface_" not in repr(after)


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
    game = create_game("zhaivra")
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
        (OverworldScreen.MAP_INSPECT, "encounter_inspection"),
        (OverworldScreen.OPTIONS, None),
        (OverworldScreen.QUIT_CONFIRMATION, None),
    ),
)
def test_each_screen_exposes_only_its_approved_screen_specific_model(
    screen,
    populated_field,
):
    game = create_game("zhaivra")
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
        "encounter_inspection",
    )

    assert tuple(
        field for field in fields if getattr(view, field) is not None
    ) == (() if populated_field is None else (populated_field,))


def test_all_deferred_and_illegal_presentation_controls_remain_disabled():
    presenter = OverworldPresenter()
    game = create_game("zhaivra")
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
    assert option(route_map, OverworldAction.INSPECT).enabled is True
    assert option(options, OverworldAction.SAVE).enabled is False
    assert option(options, OverworldAction.LOAD).enabled is False

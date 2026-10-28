import pytest

from app.content.catalog import get_drifter_spec, get_weapon_spec
from app.content.weapon_progression_spec import (
    WeaponComponentSpec,
    WeaponProgressionSpec,
    WeaponSlotSpec,
    derive_weapon_identities,
)
from app.game.game_state import GameState
from app.game.weapon_progression import WeaponProgressionService
from app.player.player_state import PlayerState


class FixedRng:
    def __init__(self, values=(), *, family_index=0):
        self.values = list(values)
        self.family_index = family_index

    def randint(self, start, end):
        value = self.values.pop(0)
        assert start <= value <= end
        return value

    def choice(self, values):
        return values[self.family_index]


def _game(*, crafting_experience=0, items=None, rng_values=()):
    lead = PlayerState(
        get_drifter_spec("branoc").create_character(),
        gold=75,
    )
    game = GameState(lead)
    assert game.party_state.arrive_at_hub(lead)
    if crafting_experience:
        game.party_state.add_crafting_experience(crafting_experience)
    if items:
        game.party_state.add_shared_items(items)
    return game, WeaponProgressionService(game, rng=FixedRng(rng_values))


@pytest.mark.parametrize(
    "slot_id,material_id",
    (
        ("blade_guard", "grade_i_metal"),
        ("grip_binding", "grade_i_fiber"),
        ("hilt_handle", "grade_i_timber"),
        ("crest_core", "grade_i_cores"),
    ),
)
def test_grade_one_improvement_spends_the_matching_material_and_awards_crafting(
    slot_id,
    material_id,
):
    game, service = _game(items={material_id: 1}, rng_values=(100,))

    result = service.improve_slot(target_drifter_id="branoc", slot_id=slot_id)

    assert result.success is True
    assert result.roll == 5
    assert result.slot_progress == 5
    assert result.material_id == material_id
    assert game.party_state.shared_items == {}
    assert game.party_state.crafting_experience == 20


def test_improvement_uses_current_grade_to_reach_gate():
    game, service = _game(
        items={"grade_i_metal": 1},
        rng_values=(100,),
    )
    state = game.player_state.signature_weapon_state
    state.set_slot_progress("blade_guard", 23)

    result = service.improve_slot(
        target_drifter_id="branoc",
        slot_id="blade_guard",
    )

    assert result.success is True
    assert result.roll == 5
    assert result.slot_progress == 25
    assert result.material_id == "grade_i_metal"
    assert game.party_state.shared_items == {}


def test_improvement_uses_next_grade_after_all_slots_unlock_the_tier():
    game, service = _game(
        crafting_experience=240,
        items={"grade_ii_metal": 2},
        rng_values=(100,),
    )
    state = game.player_state.signature_weapon_state
    for slot_id in state.slot_progress:
        state.set_slot_progress(slot_id, 25)

    result = service.improve_slot(
        target_drifter_id="branoc",
        slot_id="blade_guard",
    )

    assert result.success is True
    assert result.material_id == "grade_ii_metal"
    assert result.slot_progress == 30
    assert game.party_state.shared_items == {}


def test_rejected_improvements_do_not_spend_or_change_progress():
    game, service = _game(items={"grade_i_fiber": 2}, rng_values=(100,))

    wrong_family = service.improve_slot(
        target_drifter_id="branoc",
        slot_id="blade_guard",
    )
    assert wrong_family.success is False
    assert wrong_family.reason == "insufficient_materials"
    assert game.player_state.signature_weapon_state.slot_progress["blade_guard"] == 0
    assert game.party_state.shared_items == {"grade_i_fiber": 2}
    assert game.party_state.crafting_experience == 0

    game, service = _game(items={"grade_ii_metal": 1}, rng_values=(100,))
    game.player_state.signature_weapon_state.set_slot_progress("blade_guard", 24)
    grade_blocked = service.improve_slot(
        target_drifter_id="branoc",
        slot_id="blade_guard",
    )
    assert grade_blocked.success is False
    assert grade_blocked.reason == "insufficient_materials"
    assert game.player_state.signature_weapon_state.slot_progress["blade_guard"] == 24
    assert game.party_state.shared_items == {"grade_ii_metal": 1}


def test_tier_gate_blocks_further_progress_until_all_slots_and_crafting_meet_it():
    game, service = _game(
        crafting_experience=240,
        items={"grade_ii_metal": 1},
        rng_values=(100,),
    )
    game.player_state.signature_weapon_state.set_slot_progress("blade_guard", 25)

    result = service.improve_slot(
        target_drifter_id="branoc",
        slot_id="blade_guard",
    )

    assert result.success is False
    assert result.reason == "tier_locked"
    assert game.party_state.shared_items == {"grade_ii_metal": 1}
    assert game.party_state.crafting_experience == 240


def test_improvement_requires_an_exact_current_roster_target():
    _, service = _game(items={"grade_i_metal": 1}, rng_values=(100,))

    with pytest.raises(ValueError, match="current party"):
        service.improve_slot(target_drifter_id="azhvielle", slot_id="blade_guard")
    with pytest.raises(ValueError, match="target_drifter_id"):
        service.improve_slot(target_drifter_id=None, slot_id="blade_guard")


def test_goblin_scrap_dismantles_into_grade_one_material_without_crafting_xp():
    game, service = _game(items={"goblin_scrap": 1}, rng_values=(100,))

    result = service.dismantle(
        target_drifter_id="branoc",
        item_id="goblin_scrap",
        quantity=1,
    )

    assert result.success is True
    assert result.materials == {"grade_i_metal": 1}
    assert game.party_state.shared_items == {"grade_i_metal": 1}
    assert game.party_state.crafting_experience == 0


def test_goblin_lord_core_always_dismantles_into_one_grade_one_core():
    game, service = _game(items={"goblin_lord_core": 1})

    result = service.dismantle(
        target_drifter_id="branoc",
        item_id="goblin_lord_core",
        quantity=1,
    )

    assert result.success is True
    assert result.materials == {"grade_i_cores": 1}
    assert game.party_state.shared_items == {"grade_i_cores": 1}
    assert game.party_state.crafting_experience == 0


def test_dismantling_insufficient_loot_is_atomic():
    game, service = _game()

    result = service.dismantle(
        target_drifter_id="branoc",
        item_id="goblin_scrap",
        quantity=1,
    )

    assert result.success is False
    assert result.reason == "insufficient_items"
    assert game.party_state.shared_items == {}
    assert game.party_state.crafting_experience == 0


def test_crafting_a_floor_one_component_spends_its_material_and_awards_crafting():
    game, service = _game(items={"grade_i_metal": 1})

    result = service.craft_component(
        target_drifter_id="branoc",
        component_id="sunder_spire_blade_reinforced",
    )

    assert result.success is True
    assert game.party_state.shared_items == {
        "sunder_spire_blade_reinforced": 1,
    }
    assert game.party_state.crafting_experience == 10


def test_installing_component_consumes_new_part_and_projects_its_move_effect():
    game, service = _game(items={
        "sunder_spire_blade_reinforced": 1,
    })
    original_moves = tuple(game.player_state.combat_moves)
    original_components = game.player_state.signature_weapon_state.components

    result = service.install_component(
        target_drifter_id="branoc",
        slot_id="blade_guard",
        component_id="sunder_spire_blade_reinforced",
    )

    assert result.success is True
    assert game.player_state.signature_weapon_state.components["blade_guard"] == (
        "sunder_spire_blade_reinforced"
    )
    assert game.party_state.shared_items == {}
    assert game.player_state.combat_moves[0].power == original_moves[0].power + 2
    assert game.player_state.combat_moves[0].accuracy == original_moves[0].accuracy - 2
    assert game.player_state.combat_moves[0].target == original_moves[0].target
    assert game.player_state.combat_moves[0].scales_with == original_moves[0].scales_with
    assert game.player_state.signature_weapon_state.components["blade_guard"] != (
        original_components["blade_guard"]
    )


def test_component_identity_uses_threshold_and_returns_none_for_a_tie():
    families = ("metal", "fiber", "timber", "cores")
    slots = tuple(
        WeaponSlotSpec(f"slot_{index}", f"Slot {index}", family, f"starter_{index}")
        for index, family in enumerate(families, start=1)
    )
    components = tuple(
        WeaponComponentSpec(
            f"starter_{index}",
            f"Starter {index}",
            f"slot_{index}",
            is_starting=True,
        )
        for index in range(1, 5)
    ) + (
        WeaponComponentSpec(
            "fast_part",
            "Fast part",
            "slot_1",
            recipe_material_id="grade_i_metal",
            recipe_cost=1,
            crafting_award=1,
            physical_identity="Fast",
            physical_points=2,
        ),
        WeaponComponentSpec(
            "heavy_part",
            "Heavy part",
            "slot_2",
            recipe_material_id="grade_i_fiber",
            recipe_cost=1,
            crafting_award=1,
            physical_identity="Heavy",
            physical_points=2,
        ),
        WeaponComponentSpec(
            "more_fast",
            "More Fast",
            "slot_3",
            recipe_material_id="grade_i_timber",
            recipe_cost=1,
            crafting_award=1,
            physical_identity="Fast",
            physical_points=1,
        ),
        WeaponComponentSpec(
            "untagged_part",
            "Untagged part",
            "slot_4",
            recipe_material_id="grade_i_cores",
            recipe_cost=1,
            crafting_award=1,
        ),
    )
    progression = WeaponProgressionSpec(slots, components)
    installed = {slot.slot_id: slot.starting_component_id for slot in slots}

    installed["slot_1"] = "fast_part"
    assert derive_weapon_identities(progression, installed) == ("Fast", None)

    installed["slot_2"] = "heavy_part"
    assert derive_weapon_identities(progression, installed) == (None, None)

    installed["slot_3"] = "more_fast"
    assert derive_weapon_identities(progression, installed) == ("Fast", None)


def test_installing_unknown_slot_returns_failure_without_spending_component():
    component_id = "sunder_spire_blade_reinforced"
    game, service = _game(items={component_id: 1})

    result = service.install_component(
        target_drifter_id="branoc",
        slot_id="not_a_weapon_slot",
        component_id=component_id,
    )

    assert result.success is False
    assert result.reason == "wrong_slot"
    assert game.party_state.shared_items == {component_id: 1}

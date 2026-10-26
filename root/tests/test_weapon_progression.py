import pytest

from app.content.catalog import get_drifter_spec
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

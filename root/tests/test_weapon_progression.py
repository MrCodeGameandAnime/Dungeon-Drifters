import pytest

from app.content.catalog import get_drifter_spec, get_weapon_spec
from app.content.weapon_progression_spec import (
    IMPROVEMENT_ROLL_WEIGHT_BANDS,
    WeaponComponentSpec,
    WeaponProgressionSpec,
    WeaponSlotSpec,
    derive_weapon_identities,
    improvement_roll,
    project_weapon_stat_bonuses,
)
from app.game.game_state import GameState
from app.game.weapon_progression import WeaponProgressionService
from app.player.player_state import PlayerState
from app.player.signature_weapon_state import SignatureWeaponState


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


@pytest.mark.parametrize(
    "gate,crafting_experience,material_id,cost",
    (
        (25, 0, "grade_i_metal", 1),
        (50, 240, "grade_ii_metal", 2),
        (75, 490, "grade_iii_metal", 3),
        (100, 740, "grade_iv_metal", 4),
    ),
)
def test_improvement_clamps_at_each_quality_gate_without_overflow(
    gate,
    crafting_experience,
    material_id,
    cost,
):
    game, service = _game(
        crafting_experience=crafting_experience,
        items={material_id: cost},
        rng_values=(100,),
    )
    state = game.player_state.signature_weapon_state
    previous_gate = gate - 25
    for slot_id in state.slot_progress:
        state.set_slot_progress(slot_id, previous_gate)
    state.set_slot_progress("blade_guard", gate - 2)

    result = service.improve_slot(
        target_drifter_id="branoc",
        slot_id="blade_guard",
    )

    assert result.success is True
    assert result.roll == 5
    assert result.slot_progress == gate
    assert state.slot_progress["blade_guard"] == gate
    assert result.material_id == material_id
    assert game.party_state.shared_items == {}


@pytest.mark.parametrize("gate", (25, 50, 75))
@pytest.mark.parametrize("blocker", ("lagging_slot", "crafting_level"))
def test_next_grade_remains_locked_until_every_slot_and_crafting_meet_gate(
    gate,
    blocker,
):
    grade = gate // 25 + 1
    material_id = f"grade_{('i', 'ii', 'iii', 'iv')[grade - 1]}_metal"
    cost = grade
    required_experience = {25: 240, 50: 490, 75: 740}[gate]
    game, service = _game(
        crafting_experience=required_experience,
        items={material_id: cost},
        rng_values=(),
    )
    state = game.player_state.signature_weapon_state
    for slot_id in state.slot_progress:
        state.set_slot_progress(slot_id, gate)
    if blocker == "lagging_slot":
        state.set_slot_progress("crest_core", gate - 1)
    else:
        game.party_state._crafting_experience = required_experience - 10

    result = service.improve_slot(
        target_drifter_id="branoc",
        slot_id="blade_guard",
    )

    assert result.success is False
    assert result.reason == "tier_locked"
    assert result.attempted is False
    assert game.party_state.shared_items == {material_id: cost}
    assert state.slot_progress["blade_guard"] == gate


@pytest.mark.parametrize(
    "gate,expected_strength",
    ((0, 3), (25, 4), (50, 4), (75, 5), (100, 6)),
)
def test_quality_projection_uses_each_unlocked_tier_from_original_bonus(
    gate,
    expected_strength,
):
    progression = get_weapon_spec("sunder_spire").progression
    progress = {slot.slot_id: gate for slot in progression.slots}

    projected = project_weapon_stat_bonuses(
        progression,
        {"strength": 3},
        progress,
        tier_v_success=False,
    )

    assert projected == {"strength": expected_strength}


@pytest.mark.parametrize(
    "level,weights",
    IMPROVEMENT_ROLL_WEIGHT_BANDS,
)
def test_every_improvement_result_is_reachable_at_each_crafting_band(level, weights):
    cumulative = 0
    observed = []
    for weight in weights:
        cumulative += weight
        if weight:
            observed.append(improvement_roll(level, FixedRng((cumulative,))))

    assert observed == [1, 2, 3, 4, 5]


def test_average_improvement_roll_rises_with_crafting_level():
    expected_values = tuple(
        sum(points * weight for points, weight in enumerate(weights, start=1))
        for _, weights in IMPROVEMENT_ROLL_WEIGHT_BANDS
    )

    assert expected_values == tuple(sorted(expected_values))
    assert len(set(expected_values)) == len(expected_values)


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


def test_slot_improvement_projects_from_original_weapon_bonuses():
    game, _ = _game()
    player = game.player_state
    initial_strength = player.effective_stat("strength")
    initial_constitution = player.effective_stat("constitution")
    state = player.signature_weapon_state
    for slot_id in state.slot_progress:
        state.set_slot_progress(slot_id, 100)

    assert player.effective_stat("strength") == initial_strength + 3
    assert player.effective_stat("constitution") == initial_constitution


def test_tier_quality_and_tier_five_bonus_are_additive_and_round_half_up():
    game, _ = _game()
    player = game.player_state
    state = player.signature_weapon_state
    initial_constitution = player.effective_stat("constitution")
    for slot_id in state.slot_progress:
        state.set_slot_progress(slot_id, 100)

    assert player.effective_stat("strength") == 21
    state.mark_tier_v_success()
    assert player.effective_stat("constitution") == initial_constitution + 1


def test_stat_projection_rounds_exact_halves_up_once():
    progression = get_weapon_spec("sunder_spire").progression

    projected = project_weapon_stat_bonuses(
        progression,
        {"strength": 2},
        {
            "blade_guard": 100,
            "grip_binding": 0,
            "hilt_handle": 0,
            "crest_core": 0,
        },
        tier_v_success=False,
    )

    assert projected == {"strength": 3}


def test_tier_five_attempt_spends_configured_grade_four_materials_on_success():
    costs = {
        "grade_iv_metal": 12,
        "grade_iv_fiber": 12,
        "grade_iv_timber": 12,
        "grade_iv_cores": 12,
    }
    game, service = _game(crafting_experience=990, items=costs, rng_values=(20,))
    state = game.player_state.signature_weapon_state
    for slot_id in state.slot_progress:
        state.set_slot_progress(slot_id, 100)

    result = service.attempt_tier_v(target_drifter_id="branoc")

    assert result.success is True
    assert result.attempted is True
    assert state.tier_v_success is True
    assert game.party_state.shared_items == {}
    assert game.party_state.crafting_experience == 990


def test_tier_five_failure_consumes_materials_without_progress_or_crafting_award():
    costs = {
        "grade_iv_metal": 12,
        "grade_iv_fiber": 12,
        "grade_iv_timber": 12,
        "grade_iv_cores": 12,
    }
    game, service = _game(crafting_experience=990, items=costs, rng_values=(21,))
    state = game.player_state.signature_weapon_state
    for slot_id in state.slot_progress:
        state.set_slot_progress(slot_id, 100)

    result = service.attempt_tier_v(target_drifter_id="branoc")

    assert result.success is False
    assert result.reason == "tier_v_failed"
    assert result.attempted is True
    assert state.tier_v_success is False
    assert state.slot_progress == {slot_id: 100 for slot_id in state.slot_progress}
    assert game.party_state.shared_items == {}
    assert game.party_state.crafting_experience == 990


def test_tier_five_rejects_incomplete_requirements_without_spending_or_rolling():
    costs = {
        "grade_iv_metal": 12,
        "grade_iv_fiber": 12,
        "grade_iv_timber": 12,
        "grade_iv_cores": 12,
    }
    game, service = _game(items=costs, rng_values=())
    state = game.player_state.signature_weapon_state
    for slot_id in state.slot_progress:
        state.set_slot_progress(slot_id, 100)

    result = service.attempt_tier_v(target_drifter_id="branoc")

    assert result.success is False
    assert result.reason == "tier_locked"
    assert result.attempted is False
    assert state.tier_v_success is False
    assert game.party_state.shared_items == costs


def test_tier_five_rejects_insufficient_cost_atomically():
    costs = {
        "grade_iv_metal": 12,
        "grade_iv_fiber": 12,
        "grade_iv_timber": 12,
        "grade_iv_cores": 11,
    }
    game, service = _game(crafting_experience=990, items=costs, rng_values=())
    state = game.player_state.signature_weapon_state
    for slot_id in state.slot_progress:
        state.set_slot_progress(slot_id, 100)

    result = service.attempt_tier_v(target_drifter_id="branoc")

    assert result.success is False
    assert result.reason == "insufficient_materials"
    assert result.attempted is False
    assert game.party_state.shared_items == costs
    assert state.tier_v_success is False


def test_tier_five_rng_failure_does_not_consume_attempt_materials():
    costs = {
        "grade_iv_metal": 12,
        "grade_iv_fiber": 12,
        "grade_iv_timber": 12,
        "grade_iv_cores": 12,
    }
    game, service = _game(crafting_experience=990, items=costs, rng_values=())
    state = game.player_state.signature_weapon_state
    for slot_id in state.slot_progress:
        state.set_slot_progress(slot_id, 100)

    with pytest.raises(IndexError):
        service.attempt_tier_v(target_drifter_id="branoc")

    assert game.party_state.shared_items == costs
    assert state.tier_v_success is False


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


@pytest.mark.parametrize(
    "crafting_experience,roll,expected_yield",
    ((0, 100, 1), (990, 1, 2)),
)
def test_dismantle_yield_stays_between_one_and_authored_maximum(
    crafting_experience,
    roll,
    expected_yield,
):
    game, service = _game(
        crafting_experience=crafting_experience,
        items={"goblin_scrap": 1},
        rng_values=(roll,),
    )

    result = service.dismantle(
        target_drifter_id="branoc",
        item_id="goblin_scrap",
    )

    assert result.success is True
    assert result.materials == {"grade_i_metal": expected_yield}
    assert 1 <= sum(result.materials.values()) <= 2
    assert game.party_state.crafting_experience == crafting_experience


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


def test_crafting_installs_component_spends_material_and_awards_crafting_once():
    game, service = _game(items={"grade_i_metal": 1})
    state = game.player_state.signature_weapon_state
    state.set_slot_progress("blade_guard", 25)
    original_moves = tuple(game.player_state.combat_moves)

    result = service.craft_component(
        target_drifter_id="branoc",
        component_id="sunder_spire_blade_reinforced",
    )

    assert result.success is True
    assert result.slot_id == "blade_guard"
    assert state.components["blade_guard"] == "sunder_spire_blade_reinforced"
    assert state.slot_progress["blade_guard"] == 25
    assert game.party_state.shared_items == {}
    assert game.party_state.crafting_experience == 10
    assert game.player_state.combat_moves[0].power == original_moves[0].power + 2
    assert game.player_state.combat_moves[0].accuracy == original_moves[0].accuracy - 2


def test_crafting_an_already_installed_component_is_rejected_without_mutation():
    game, service = _game(items={"grade_i_metal": 1})
    state = game.player_state.signature_weapon_state
    state.install_component("blade_guard", "sunder_spire_blade_reinforced")
    before_snapshot = game.snapshot()

    result = service.craft_component(
        target_drifter_id="branoc",
        component_id="sunder_spire_blade_reinforced",
    )

    assert result.success is False
    assert result.reason == "already_installed"
    assert game.snapshot() == before_snapshot


def test_crafting_a_wrong_weapon_component_is_rejected_without_mutation():
    game, service = _game(items={"grade_i_metal": 1})
    before_snapshot = game.snapshot()

    result = service.craft_component(
        target_drifter_id="branoc",
        component_id="needle_focus_fitted",
    )

    assert result.success is False
    assert result.reason == "unknown_component"
    assert game.snapshot() == before_snapshot


def test_replacing_component_removes_direct_effect_and_keeps_learned_technique():
    game, _service = _game()
    player = game.player_state
    state_snapshot = player.signature_weapon_state.snapshot()
    state_snapshot["components"]["blade_guard"] = "sunder_spire_blade_reinforced"
    state_snapshot["learned_technique_ids"] = ["controlled_test_technique"]
    progression = get_weapon_spec("sunder_spire").progression
    player._signature_weapon_state = SignatureWeaponState.from_snapshot(
        state_snapshot,
        progression,
    )
    reinforced_power = next(
        move.power for move in player.combat_moves
        if move.name == "Crestgrave Reaping"
    )
    baseline_player = PlayerState(get_drifter_spec("branoc").create_character())
    baseline_power = next(
        move.power for move in baseline_player.combat_moves
        if move.name == "Crestgrave Reaping"
    )

    player.signature_weapon_state.install_component(
        "blade_guard",
        "sunder_spire_blade",
    )
    assert reinforced_power == baseline_power + 2
    assert next(
        move.power for move in player.combat_moves
        if move.name == "Crestgrave Reaping"
    ) == baseline_power
    assert player.signature_weapon_state.learned_technique_ids == (
        "controlled_test_technique",
    )
    assert game.party_state.shared_items == {}


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


def test_crafting_without_required_material_is_atomic():
    game, service = _game()
    before_snapshot = game.snapshot()

    result = service.craft_component(
        target_drifter_id="branoc",
        component_id="sunder_spire_blade_reinforced",
    )

    assert result.success is False
    assert result.reason == "insufficient_materials"
    assert game.snapshot() == before_snapshot

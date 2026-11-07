import random

import pytest

from app.content.armor_spec import (
    ARMOR_RARITIES,
    FLOOR_RARITY_POLICIES,
    MODIFIER_DEFINITIONS,
    ArmorModifierSpec,
    ArmorRaritySpec,
    FloorRarityPolicySpec,
    get_armor_rarity,
    get_floor_rarity_policy,
    validate_armor_content,
)
from app.content.equipment_spec import (
    EQUIPMENT_TEMPLATES,
    EquipmentTemplateSpec,
    get_equipment_template,
)
from app.game.armor_generation import ArmorGenerationService
from app.items.equipment import EquipmentInstance


class _ScriptedRng:
    def __init__(self, values):
        self._values = iter(values)

    def randrange(self, stop):
        value = next(self._values, 0)
        assert 0 <= value < stop
        return value


def test_rarity_capacity_and_floor_policy_are_authored_and_progressive():
    assert tuple(
        rarity.modifier_capacity for rarity in ARMOR_RARITIES
    ) == (1, 2, 3, 4, 5)
    assert tuple(
        max(
            rarity.modifier_capacity
            for rarity_id, weight in get_floor_rarity_policy(floor).rarity_weights_bps
            if weight
            for rarity in (get_armor_rarity(rarity_id),)
        )
        for floor in range(1, 11)
    ) == tuple(sorted(
        max(
            rarity.modifier_capacity
            for rarity_id, weight in get_floor_rarity_policy(floor).rarity_weights_bps
            if weight
            for rarity in (get_armor_rarity(rarity_id),)
        )
        for floor in range(1, 11)
    ))
    assert "legendary" not in dict(get_floor_rarity_policy(1).rarity_weights_bps)
    assert dict(get_floor_rarity_policy(10).rarity_weights_bps)["legendary"] > 0


@pytest.mark.parametrize(
    ("floor", "highest_rarity"),
    (
        (1, "common"),
        (2, "uncommon"),
        (3, "uncommon"),
        (4, "rare"),
        (5, "rare"),
        (6, "epic"),
        (7, "epic"),
        (8, "legendary"),
        (9, "legendary"),
        (10, "legendary"),
    ),
)
def test_each_floor_generates_only_its_authored_rarity_ceiling(floor, highest_rarity):
    policy = get_floor_rarity_policy(floor)
    weights = dict(policy.rarity_weights_bps)
    assert sum(weights.values()) == 10000
    assert max(
        (get_armor_rarity(rarity_id).modifier_capacity
         for rarity_id, weight in weights.items() if weight),
    ) == get_armor_rarity(highest_rarity).modifier_capacity

    generated = ArmorGenerationService(
        rng=_ScriptedRng([sum(weights.values()) - 1])
    ).generate(
        template_id="field_helm",
        floor=floor,
        source_id=f"floor_{floor}_reward_policy_01",
        instance_id=f"00000000-0000-4000-8000-{floor:012d}",
    )

    template = get_equipment_template(generated.definition_id)
    rarity = get_armor_rarity(generated.rarity)
    assert generated.rarity == highest_rarity
    assert generated.rarity in weights and weights[generated.rarity] > 0
    assert set(generated.modifier_slots).issubset(rarity.modifier_grades)
    assert all(
        minimum <= generated.stat_bonuses[stat] <= maximum
        for stat, minimum, maximum in template.stat_ranges
    )
    for modifier_id in generated.modifier_slots.values():
        modifier = next(
            modifier
            for modifier in MODIFIER_DEFINITIONS
            if modifier.modifier_id == modifier_id
        )
        assert template.slot_id in modifier.compatible_slots


def test_authored_armor_content_has_compatible_modifiers_for_each_grade():
    assert {modifier.grade for modifier in MODIFIER_DEFINITIONS} == {
        "I", "II", "III", "IV", "V"
    }
    validate_armor_content(
        templates=EQUIPMENT_TEMPLATES,
        rarities=ARMOR_RARITIES,
        modifiers=MODIFIER_DEFINITIONS,
        policies=FLOOR_RARITY_POLICIES,
    )


def test_invalid_duplicate_modifier_and_bad_floor_policy_are_rejected():
    modifier = MODIFIER_DEFINITIONS[0]
    with pytest.raises(ValueError, match="modifier IDs must be unique"):
        validate_armor_content(
            templates=EQUIPMENT_TEMPLATES,
            rarities=ARMOR_RARITIES,
            modifiers=(modifier, modifier),
            policies=FLOOR_RARITY_POLICIES,
        )

    with pytest.raises(ValueError, match="sum to 10000"):
        FloorRarityPolicySpec(
            floor=1,
            rarity_weights_bps=(("common", 9999),),
            modifier_chance_percent=35,
        )


def test_armor_catalog_requires_fixed_ring_and_pendant_definitions():
    with pytest.raises(ValueError, match="Ring and Pendant"):
        validate_armor_content(
            templates=tuple(
                template
                for template in EQUIPMENT_TEMPLATES
                if template.slot_id != "ring"
            ),
            rarities=ARMOR_RARITIES,
            modifiers=MODIFIER_DEFINITIONS,
            policies=FLOOR_RARITY_POLICIES,
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("family", "jewelry", "family"),
        ("stat_ranges", (("constitution", 3, 2),), "minimum exceeds maximum"),
        ("slot_id", "ring", "category does not match"),
        ("definition_id", "Bad ID", "definition ID is invalid"),
        ("dismantle_yields", (("unknown_material", 1),), "unknown dismantle material"),
    ),
)
def test_authored_equipment_template_rejects_invalid_shape(field, value, message):
    kwargs = {
        "definition_id": "test_armor",
        "name": "Test Armor",
        "category": "armor",
        "slot_id": "helm",
        "stat_ranges": (("constitution", 1, 2),),
        "family": "heavy",
        "material_id": "grade_i_metal",
        "upgrade_stat_bonuses": (("constitution", 1),),
    }
    kwargs[field] = value
    with pytest.raises(ValueError, match=message):
        EquipmentTemplateSpec(**kwargs)


def test_modifier_catalog_rejects_unsupported_effects_and_unknown_rarity_refs():
    with pytest.raises(TypeError, match="existing passive combat effects"):
        ArmorModifierSpec(
            "invalid_effect",
            "Invalid Effect",
            "I",
            ("helm",),
            (object(),),
        )

    unknown_rarity_policy = FloorRarityPolicySpec(
        1,
        (("unlisted_rarity", 10000),),
        20,
    )
    with pytest.raises(ValueError, match="unknown rarity"):
        validate_armor_content(
            templates=EQUIPMENT_TEMPLATES,
            rarities=ARMOR_RARITIES,
            modifiers=MODIFIER_DEFINITIONS,
            policies=(unknown_rarity_policy, *FLOOR_RARITY_POLICIES[1:]),
        )


def test_generator_is_reproducible_and_persists_materialized_results():
    args = {
        "template_id": "field_helm",
        "floor": 10,
        "source_id": "floor_ten_reward_01",
        "instance_id": "00000000-0000-4000-8000-000000000301",
    }
    first = ArmorGenerationService(rng=random.Random(731)).generate(**args)
    second = ArmorGenerationService(rng=random.Random(731)).generate(**args)

    assert first.snapshot() == second.snapshot()
    restored = EquipmentInstance.from_snapshot(first.snapshot())
    assert restored.snapshot() == first.snapshot()
    assert restored.rarity == first.rarity
    assert restored.modifier_slots == first.modifier_slots


@pytest.mark.parametrize(
    ("value", "message"),
    (
        (True, "non-integer"),
        (-1, "out-of-range"),
        (10000, "out-of-range"),
        ("0", "non-integer"),
    ),
)
def test_generator_rejects_malformed_injected_rng_results(value, message):
    class InvalidRng:
        def randrange(self, stop):
            return value

    with pytest.raises(ValueError, match=message):
        ArmorGenerationService(rng=InvalidRng()).generate(
            template_id="field_helm",
            floor=1,
            source_id="floor_one_reward_01",
            instance_id="00000000-0000-4000-8000-000000000399",
        )


def test_equipped_generated_modifier_projects_into_existing_combat_passives():
    from app.content.catalog import get_drifter_spec
    from app.game.game_state import GameState
    from app.player.player_state import PlayerState

    game = GameState(
        PlayerState(get_drifter_spec("branoc").create_character())
    )
    armor = EquipmentInstance.create(
        instance_id="00000000-0000-4000-8000-000000000304",
        definition_id="field_helm",
        source_id="floor_ten_reward_03",
        secured=False,
        stat_bonuses={"constitution": 2},
        rarity="legendary",
        modifier_slots={"I": "bastion_grade_i"},
    )
    game.party_state.add_equipment_instance(armor)
    refs = game.player_state.equipped_equipment_ids
    refs["helm"] = armor.instance_id
    game.player_state._set_equipped_equipment_ids(refs)
    game._bind_equipment_state()

    effect = game.player_state.combat_passive_effects[-1]

    assert effect.kind.value == "mitigation"
    assert effect.value == 1
    assert effect.damage_class.value == "physical"
    assert game.clone().player_state.combat_passive_effects[-1] == effect


def test_legendary_generation_can_materialize_each_grade_once():
    generated = ArmorGenerationService(rng=_ScriptedRng([9999])).generate(
        template_id="field_helm",
        floor=10,
        source_id="floor_ten_reward_02",
        instance_id="00000000-0000-4000-8000-000000000302",
    )

    assert generated.rarity == "legendary"
    assert tuple(generated.modifier_slots) == ("I", "II", "III", "IV", "V")
    assert len(set(generated.modifier_slots)) == 5


@pytest.mark.parametrize("template_id", ("iron_ring", "wayfinder_pendant"))
def test_static_accessories_are_not_procedural_armor(template_id):
    with pytest.raises(ValueError, match="armor template"):
        ArmorGenerationService(rng=random.Random(1)).generate(
            template_id=template_id,
            floor=10,
            source_id="test_reward_01",
            instance_id="00000000-0000-4000-8000-000000000303",
        )


def test_modifier_schema_requires_valid_armor_effect_contract():
    with pytest.raises(ValueError, match="compatible armor slot"):
        ArmorModifierSpec(
            modifier_id="ring_only_modifier",
            name="Ring Only Modifier",
            grade="I",
            compatible_slots=("ring",),
            effects=MODIFIER_DEFINITIONS[0].effects,
        )

    with pytest.raises(ValueError, match="modifier capacity"):
        ArmorRaritySpec("common", "Common", modifier_capacity=0)

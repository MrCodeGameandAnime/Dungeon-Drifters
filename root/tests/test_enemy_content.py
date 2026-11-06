from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from app.combat.move import (
    DamageComponentIdentity,
    DamageType,
    Move,
    MoveKind,
    ResourceType,
    ScalingAttribute,
    TargetType,
)
from app.content.catalog import (
    ENEMY_SPECS,
    _build_enemy_catalog,
    create_enemy_definition,
    create_enemy_state,
    get_enemy_spec,
    get_encounter_spec,
)
from app.content.encounter_spec import EncounterSpec
from app.content.enemy_spec import EnemySpec, EnemyTierSpec, StatBlockSpec
from app.enemies.definition import EnemyBehavior, EnemyCapability, EnemyRank, EnemyRole
from app.enemies.state import EnemyState
from tools.generate_content_catalog import (
    OUTPUT_PATH,
    discover_drifter_ids,
    discover_encounter_ids,
    discover_enemy_ids,
    discover_route_ids,
    discover_recruitment_event_ids,
    discover_weapon_ids,
    render_catalog,
)


EXPECTED_IDS = (
    "goblin",
    "goblin_elite",
    "goblin_lord",
    "goblin_shaman",
    "goblin_warrior",
)
EXPECTED_WEAPON_IDS = (
    "needle_of_plain_iron",
    "sathren",
    "sky_needle",
    "sunder_spire",
)
EXPECTED_DRIFTER_IDS = ("azhvielle", "branoc", "joruun", "zhaivra")
EXPECTED_ENCOUNTER_IDS = (
    "dungeon_goblin_quad",
    "dungeon_goblin_trio",
    "floor_two_cave_in",
    "surface_elite_patrol",
    "surface_goblin_lord",
    "surface_goblin_pair",
    "surface_goblin_solo",
    "surface_shaman_pair",
    "surface_shaman_solo",
    "surface_warrior_pair",
    "surface_warrior_solo",
)
EXPECTED_ROUTE_IDS = ("floor_one", "floor_two", "surface")


def sample_move(name="Test Strike"):
    return Move(
        name=name,
        kind=MoveKind.DAMAGE,
        resource_type=ResourceType.NONE,
        resource_cost=0,
        power=1,
        scales_with=(ScalingAttribute.STRENGTH,),
        accuracy=100,
        target=TargetType.ENEMY,
        damage_type=DamageType.PHYSICAL,
        mechanic="basic_attack",
        description="A test strike.",
    )


def sample_spec(**overrides):
    values = {
        "archetype_id": "test_enemy",
        "name": "Test Enemy",
        "stats": StatBlockSpec(1, 1, 1, 1, 1, 1),
        "hp": 1,
        "mana": 0,
        "exp_reward": 0,
        "gold_reward": 0,
        "rank": EnemyRank.COMMON,
        "role": EnemyRole.MELEE_SKIRMISHER,
        "behavior": EnemyBehavior.AGGRESSIVE,
        "capabilities": frozenset({EnemyCapability.BASIC_ATTACKS}),
        "moves": (sample_move(),),
    }
    values.update(overrides)
    return EnemySpec(**values)


def test_generated_enemy_catalog_is_deterministic_and_current():
    assert discover_enemy_ids() == EXPECTED_IDS
    assert tuple(spec.archetype_id for spec in ENEMY_SPECS) == EXPECTED_IDS
    assert OUTPUT_PATH.read_text(encoding="utf-8") == render_catalog(
        EXPECTED_IDS,
        EXPECTED_WEAPON_IDS,
        EXPECTED_DRIFTER_IDS,
        EXPECTED_ENCOUNTER_IDS,
        EXPECTED_ROUTE_IDS,
        discover_recruitment_event_ids(),
    )
    assert discover_weapon_ids() == EXPECTED_WEAPON_IDS
    assert discover_drifter_ids() == EXPECTED_DRIFTER_IDS
    assert discover_encounter_ids() == EXPECTED_ENCOUNTER_IDS
    assert discover_route_ids() == EXPECTED_ROUTE_IDS


def test_floor_two_cave_in_encounter_authors_a_bounded_physical_threat():
    encounter = get_encounter_spec("floor_two_cave_in")

    assert encounter.enemy_archetype_ids == ("goblin", "goblin_warrior")
    assert encounter.cave_in_power == 20


def test_item_drop_specs_validate_probability_quantity_and_authored_id():
    import app.content.enemy_spec as enemy_content

    drop_type = getattr(enemy_content, "ItemDropSpec", None)
    assert drop_type is not None
    drop = drop_type("grade_ii_metal", 2, 2000)
    assert (drop.item_id, drop.quantity, drop.chance_bps) == (
        "grade_ii_metal",
        2,
        2000,
    )

    for item_id, quantity, chance in (
        ("bad-id", 1, 2000),
        ("grade_ii_metal", 0, 2000),
        ("grade_ii_metal", True, 2000),
        ("grade_ii_metal", 1, -1),
        ("grade_ii_metal", 1, 10001),
        ("grade_ii_metal", 1, True),
    ):
        with pytest.raises((TypeError, ValueError)):
            drop_type(item_id, quantity, chance)


def test_tier_one_content_authors_all_grade_two_material_families():
    material_drops = {
        drop.item_id: drop.chance_bps
        for enemy in ENEMY_SPECS
        for profile in enemy.tier_profiles
        if profile.tier == 1
        for drop in profile.item_drops
    }

    assert {
        "grade_ii_metal": 2000,
        "grade_ii_fiber": 2000,
        "grade_ii_timber": 2000,
        "grade_ii_cores": 1000,
    }.items() <= material_drops.items()


def test_encounter_drop_tables_preserve_each_enemy_instance_and_tier():
    import app.content.catalog as catalog

    get_tables = getattr(catalog, "get_encounter_item_drop_tables", None)
    assert get_tables is not None
    tables = get_tables("floor_two_cave_in", tier=1)
    assert len(tables) == 2
    assert tables[0][0].item_id == "grade_ii_metal"
    assert tables[1][0].item_id == "grade_ii_timber"


@pytest.mark.parametrize("power", (True, 0, -1, 1.5))
def test_encounter_rejects_invalid_cave_in_power(power):
    expected_error = TypeError if isinstance(power, bool) or not isinstance(power, int) else ValueError
    with pytest.raises(expected_error, match="cave_in_power"):
        EncounterSpec("bad_hazard", ("goblin",), cave_in_power=power)


def test_generator_rejects_directory_and_authored_id_mismatch(tmp_path):
    enemy_path = tmp_path / "wrong_directory" / "enemy.py"
    enemy_path.parent.mkdir()
    enemy_path.write_text(
        'ENEMY = EnemySpec(archetype_id="authored_id")\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="directory ID"):
        discover_enemy_ids(tmp_path)


@pytest.mark.parametrize("invalid_id", ("class", "bad-name"))
def test_generator_rejects_non_importable_content_ids(tmp_path, invalid_id):
    enemy_path = tmp_path / invalid_id / "enemy.py"
    enemy_path.parent.mkdir()
    enemy_path.write_text(
        f'ENEMY = EnemySpec(archetype_id="{invalid_id}")\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Python module names"):
        discover_enemy_ids(tmp_path)
    with pytest.raises(ValueError, match="Python module names"):
        render_catalog((invalid_id,))


def test_enemy_specs_and_stat_blocks_are_immutable():
    spec = get_enemy_spec("goblin")

    with pytest.raises(FrozenInstanceError):
        spec.name = "Changed"
    with pytest.raises(FrozenInstanceError):
        spec.stats.strength = 99


@pytest.mark.parametrize("archetype_id", EXPECTED_IDS)
@pytest.mark.parametrize("tier", (0, 1))
def test_specs_create_fresh_definitions_and_runtime_state(archetype_id, tier):
    spec = get_enemy_spec(archetype_id)
    first_definition = spec.create_definition(tier=tier)
    second_definition = spec.create_definition(tier=tier)
    first = create_enemy_state(archetype_id, tier=tier)
    second = create_enemy_state(archetype_id, tier=tier)

    assert first_definition is not second_definition
    assert first_definition.combat_moves is not second_definition.combat_moves
    assert first_definition.combat_moves == second_definition.combat_moves == spec.moves
    assert first is not second
    assert first.definition is not second.definition
    assert first.permanent_stats is not second.permanent_stats
    assert first.health is not second.health
    assert first.mana_resource is not second.mana_resource
    assert first.super_resource is not second.super_resource
    original_second_hp = second.health.current
    original_second_mana = second.mana_resource.current
    original_second_super = second.super_resource.current

    first.health.take_damage(1)
    first.mana_resource.spend(1)
    first.super_resource.gain(1)

    assert second.health.current == original_second_hp
    assert second.mana_resource.current == original_second_mana
    assert second.super_resource.current == original_second_super


@pytest.mark.parametrize(
    "field, value, error",
    (
        ("archetype_id", "Goblin Lord", ValueError),
        ("archetype_id", "class", ValueError),
        ("archetype_id", "", ValueError),
        ("name", " ", ValueError),
        ("stats", object(), TypeError),
        ("hp", 0, ValueError),
        ("hp", True, TypeError),
        ("mana", -1, ValueError),
        ("exp_reward", True, TypeError),
        ("gold_reward", -1, ValueError),
        ("rank", "common", TypeError),
        ("role", "brute", TypeError),
        ("behavior", "aggressive", TypeError),
        ("capabilities", (EnemyCapability.BASIC_ATTACKS,), TypeError),
        ("moves", [sample_move()], TypeError),
        ("moves", (), ValueError),
        ("moves", (object(),), TypeError),
        ("supported_tiers", [0], TypeError),
        ("supported_tiers", (False,), TypeError),
        ("supported_tiers", (0, 1), ValueError),
        ("supported_tiers", (1,), ValueError),
        ("supported_tiers", (0, 0), ValueError),
        ("tier_profiles", [object()], TypeError),
        (
            "damage_resistances",
            [(DamageComponentIdentity.ELEMENTAL, "fire")],
            TypeError,
        ),
        (
            "damage_resistances",
            ((DamageComponentIdentity.PHYSICAL, "fire"),),
            ValueError,
        ),
        (
            "damage_weaknesses",
            ((DamageComponentIdentity.ALCHEMICAL, ""),),
            ValueError,
        ),
        (
            "damage_resistances",
            (
                (DamageComponentIdentity.ELEMENTAL, "fire"),
                (DamageComponentIdentity.ELEMENTAL, "fire"),
            ),
            ValueError,
        ),
    ),
)
def test_enemy_spec_rejects_invalid_authored_values(field, value, error):
    with pytest.raises(error):
        sample_spec(**{field: value})


def test_enemy_spec_rejects_duplicate_move_names():
    move = sample_move()

    with pytest.raises(ValueError, match="unique names"):
        sample_spec(moves=(move, replace(move)))


@pytest.mark.parametrize("value", (True, False, -1, "0", None))
def test_stat_block_rejects_invalid_values(value):
    error = TypeError if isinstance(value, (bool, str)) or value is None else ValueError

    with pytest.raises(error):
        StatBlockSpec(value, 1, 1, 1, 1, 1)


def test_catalog_rejects_directory_mismatch_and_duplicate_ids():
    spec = sample_spec()

    with pytest.raises(ValueError, match="directory ID"):
        _build_enemy_catalog((("wrong_directory", spec),))
    with pytest.raises(ValueError, match="duplicate enemy archetype"):
        _build_enemy_catalog(
            ((spec.archetype_id, spec), (spec.archetype_id, spec))
        )


def test_unknown_enemy_and_unsupported_tier_fail_explicitly():
    with pytest.raises(ValueError, match="unknown enemy archetype"):
        get_enemy_spec("unknown")
    with pytest.raises(ValueError, match="does not support tier 2"):
        create_enemy_definition("goblin", tier=2)


@pytest.mark.parametrize(
    "field, value, error",
    (
        ("tier", True, TypeError),
        ("tier", 0, ValueError),
        ("tier", -1, ValueError),
        ("stats", object(), TypeError),
        ("hp", 0, ValueError),
        ("mana", -1, ValueError),
    ),
)
def test_enemy_tier_profile_rejects_invalid_authored_values(field, value, error):
    values = {
        "tier": 1,
        "stats": StatBlockSpec(2, 2, 2, 2, 2, 2),
        "hp": 2,
        "mana": 0,
    }
    values[field] = value

    with pytest.raises(error):
        EnemyTierSpec(**values)


def test_enemy_spec_requires_tier_profiles_to_match_supported_tiers():
    profile = EnemyTierSpec(
        tier=1,
        stats=StatBlockSpec(2, 2, 2, 2, 2, 2),
        hp=2,
        mana=0,
    )

    with pytest.raises(ValueError, match="match supported_tiers"):
        sample_spec(supported_tiers=(0, 1))

    with pytest.raises(ValueError, match="match supported_tiers"):
        sample_spec(tier_profiles=(profile,))

    with pytest.raises(ValueError, match="unique"):
        sample_spec(
            supported_tiers=(0, 1),
            tier_profiles=(profile, profile),
        )

    with pytest.raises(ValueError, match="ordered"):
        sample_spec(
            supported_tiers=(0, 1, 2),
            tier_profiles=(
                profile,
                EnemyTierSpec(
                    tier=2,
                    stats=StatBlockSpec(3, 3, 3, 3, 3, 3),
                    hp=3,
                    mana=0,
                ),
            )[::-1],
        )


def test_enemy_spec_rejects_resistance_and_weakness_for_same_identity():
    identity = (DamageComponentIdentity.ELEMENTAL, "fire")

    with pytest.raises(ValueError, match="cannot resist and be weak"):
        sample_spec(
            damage_resistances=(identity,),
            damage_weaknesses=(identity,),
        )


def test_enemy_identity_modifiers_are_preserved_in_runtime_state():
    spec = sample_spec(
        damage_resistances=((DamageComponentIdentity.ELEMENTAL, "fire"),),
        damage_weaknesses=((DamageComponentIdentity.ALCHEMICAL, "poison"),),
    )
    state = EnemyState(spec.create_definition())

    assert state.damage_resistances == (
        (DamageComponentIdentity.ELEMENTAL, "fire"),
    )
    assert state.damage_weaknesses == (
        (DamageComponentIdentity.ALCHEMICAL, "poison"),
    )


def test_definition_creation_preserves_unknown_id_precedence():
    with pytest.raises(ValueError, match="unknown enemy archetype"):
        create_enemy_definition("unknown", tier=True)

    with pytest.raises(TypeError, match="enemy tier must be an integer"):
        create_enemy_state("unknown", tier=True)


def test_generated_catalog_contains_no_runtime_discovery_code():
    source = Path(OUTPUT_PATH).read_text(encoding="utf-8")

    assert "pathlib" not in source
    assert "pkgutil" not in source
    assert "importlib" not in source

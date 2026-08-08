from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from app.combat.move import (
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
)
from app.content.enemy_spec import EnemySpec, StatBlockSpec
from app.enemies.definition import EnemyBehavior, EnemyCapability, EnemyRank, EnemyRole
from tools.generate_content_catalog import (
    OUTPUT_PATH,
    discover_drifter_ids,
    discover_enemy_ids,
    discover_route_ids,
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
EXPECTED_ROUTE_IDS = ("surface",)


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
        EXPECTED_ROUTE_IDS,
    )
    assert discover_weapon_ids() == EXPECTED_WEAPON_IDS
    assert discover_drifter_ids() == EXPECTED_DRIFTER_IDS
    assert discover_route_ids() == EXPECTED_ROUTE_IDS


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
def test_specs_create_fresh_definitions_and_runtime_state(archetype_id):
    spec = get_enemy_spec(archetype_id)
    first_definition = spec.create_definition()
    second_definition = spec.create_definition()
    first = create_enemy_state(archetype_id)
    second = create_enemy_state(archetype_id)

    assert first_definition is not second_definition
    assert first_definition.combat_moves is not second_definition.combat_moves
    assert first_definition.combat_moves == second_definition.combat_moves == spec.moves
    assert first is not second
    assert first.definition is not second.definition
    assert first.permanent_stats is not second.permanent_stats
    assert first.health is not second.health
    assert first.mana_resource is not second.mana_resource
    assert first.super_resource is not second.super_resource


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
    with pytest.raises(ValueError, match="does not support tier 1"):
        create_enemy_definition("goblin", tier=1)


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

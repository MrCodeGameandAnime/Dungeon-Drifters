from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

import app.player.character as character_module
from app.content.catalog import (
    DRIFTER_SPECS,
    _build_drifter_catalog,
    create_drifter,
    get_drifter_spec,
    get_drifter_spec_by_choice,
)
from app.content.drifter_spec import ClassMechanicSpec, DrifterStatSpec
from app.player.character import Character
from app.player.character_run_state import PreparedPayloadId, RunItemId
from app.player.player_state import PlayerState
from tools.generate_content_catalog import (
    OUTPUT_PATH,
    discover_drifter_ids,
    discover_enemy_ids,
    discover_weapon_ids,
    render_catalog,
)


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_DRIFTERS = (
    ("branoc", "1", "Brawler", "sunder_spire"),
    ("azhvielle", "2", "Black Mage", "needle_of_plain_iron"),
    ("zhaivra", "3", "Rogue Archer", "sathren"),
    ("joruun", "4", "Monk", "sky_needle"),
)
GENERATED_ORDER = ("azhvielle", "branoc", "joruun", "zhaivra")


def test_drifter_catalog_matches_the_independent_identity_contract():
    assert tuple(
        (spec.drifter_id, spec.choice, spec.archetype_name, spec.starting_weapon_id)
        for spec in DRIFTER_SPECS
    ) == EXPECTED_DRIFTERS
    assert discover_drifter_ids() == GENERATED_ORDER

    for drifter_id, choice, _archetype, _weapon in EXPECTED_DRIFTERS:
        spec = get_drifter_spec(drifter_id)
        assert get_drifter_spec_by_choice(choice) is spec
    assert get_drifter_spec_by_choice("5") is None


def test_generated_catalog_is_current_for_all_flattened_content():
    expected = render_catalog(
        discover_enemy_ids(),
        discover_weapon_ids(),
        discover_drifter_ids(),
    )

    assert OUTPUT_PATH.read_text(encoding="utf-8") == expected


@pytest.mark.parametrize(
    "drifter_id",
    tuple(value[0] for value in EXPECTED_DRIFTERS),
)
def test_drifter_factory_builds_fresh_generic_runtime_graphs(drifter_id):
    spec = get_drifter_spec(drifter_id)
    first = create_drifter(drifter_id)
    second = create_drifter(drifter_id)
    first_player = PlayerState(first)
    second_player = PlayerState(second)

    assert type(first) is type(second) is Character
    assert first is not second
    assert first.profile is second.profile is None
    assert first.permanent_stats is not second.permanent_stats
    assert first.health is not second.health
    assert first.mana_resource is not second.mana_resource
    assert first.level_state is not second.level_state
    assert first.exp_state is not second.exp_state
    assert first_player.super_resource is not second_player.super_resource
    assert first_player.inventory is not second_player.inventory
    assert first_player.character_run_state is not second_player.character_run_state
    assert first.combat_moves is not second.combat_moves
    assert first.combat_moves is not spec.combat_moves
    assert second.combat_moves is not spec.combat_moves
    assert tuple(first.combat_moves) == tuple(second.combat_moves) == spec.combat_moves
    assert all(
        first_move is authored_move is second_move
        for first_move, authored_move, second_move in zip(
            first.combat_moves,
            spec.combat_moves,
            second.combat_moves,
        )
    )
    assert first.class_mechanic is not second.class_mechanic
    assert first.starting_equipment is not second.starting_equipment
    assert first.starting_equipment["weapon"] is not second.starting_equipment["weapon"]


@pytest.mark.parametrize(
    "drifter_id",
    tuple(value[0] for value in EXPECTED_DRIFTERS),
)
def test_profile_construction_attaches_the_canonical_selected_identity(drifter_id):
    spec = get_drifter_spec(drifter_id)
    character = spec.create_character()

    assert character.profile is spec
    assert character.display_name == spec.short_name
    assert character.full_display_name == spec.display_name


def test_zhaivra_run_defaults_are_authored_once_and_runtime_isolated():
    spec = get_drifter_spec("zhaivra")
    first = create_drifter("zhaivra")
    second = create_drifter("zhaivra")

    assert spec.starting_run_inventory == (
        (RunItemId.EMBER_SHARD, 1),
        (RunItemId.DEEP_COAL, 1),
        (RunItemId.NIGHT_BERRY, 1),
    )
    assert spec.starting_prepared_payloads == (
        (PreparedPayloadId.INFUSED_BARB, None),
    )
    first.starting_run_inventory[RunItemId.EMBER_SHARD] = 0
    first.starting_prepared_payloads[PreparedPayloadId.INFUSED_BARB] = "changed"

    assert second.starting_run_inventory[RunItemId.EMBER_SHARD] == 1
    assert second.starting_prepared_payloads[PreparedPayloadId.INFUSED_BARB] is None


def test_drifter_specs_and_nested_authored_values_are_immutable():
    spec = get_drifter_spec("branoc")

    with pytest.raises(FrozenInstanceError):
        spec.display_name = "Changed"
    with pytest.raises(FrozenInstanceError):
        spec.stats.strength = 99
    with pytest.raises(FrozenInstanceError):
        spec.class_mechanic.name = "Changed"
    with pytest.raises(TypeError):
        DRIFTER_SPECS[0] = spec


@pytest.mark.parametrize(
    "field,value,error",
    (
        ("drifter_id", "Bad ID", ValueError),
        ("drifter_id", "class", ValueError),
        ("choice", "0", ValueError),
        ("choice", True, TypeError),
        ("archetype_name", " ", ValueError),
        ("stats", object(), TypeError),
        ("combat_moves", [], TypeError),
        ("combat_moves", (), ValueError),
        ("combat_moves", (object(),), TypeError),
        ("class_mechanic", object(), TypeError),
        ("starting_weapon_id", "Bad Weapon", ValueError),
        ("starting_run_inventory", [], TypeError),
        ("starting_run_inventory", ((RunItemId.EMBER_SHARD,),), TypeError),
        ("starting_run_inventory", ((RunItemId.EMBER_SHARD, True),), TypeError),
        ("starting_run_inventory", ((RunItemId.EMBER_SHARD, -1),), ValueError),
        ("starting_prepared_payloads", [], TypeError),
        ("starting_prepared_payloads", ((PreparedPayloadId.INFUSED_BARB,),), TypeError),
        ("starting_prepared_payloads", ((PreparedPayloadId.INFUSED_BARB, "fire"),), ValueError),
    ),
)
def test_drifter_spec_rejects_invalid_authored_values(field, value, error):
    with pytest.raises(error):
        replace(get_drifter_spec("branoc"), **{field: value})


def test_nested_spec_values_enforce_level_one_and_text_contracts():
    with pytest.raises(ValueError, match="total must be 60"):
        DrifterStatSpec(1, 1, 1, 1, 1, 1)
    with pytest.raises(TypeError):
        DrifterStatSpec(True, 10, 10, 10, 10, 10)
    with pytest.raises(ValueError):
        ClassMechanicSpec(" ", "description")


def test_drifter_catalog_rejects_mismatch_and_duplicate_authorities():
    branoc = get_drifter_spec("branoc")
    azhvielle = get_drifter_spec("azhvielle")

    with pytest.raises(ValueError, match="directory ID"):
        _build_drifter_catalog((("wrong", branoc),))
    with pytest.raises(ValueError, match="duplicate Drifter ID"):
        _build_drifter_catalog((("branoc", branoc), ("branoc", branoc)))
    with pytest.raises(ValueError, match="duplicate Drifter choice"):
        duplicate_choice = replace(azhvielle, choice=branoc.choice)
        _build_drifter_catalog((("branoc", branoc), ("azhvielle", duplicate_choice)))


def test_unknown_drifter_fails_explicitly():
    with pytest.raises(ValueError, match="unknown Drifter ID"):
        get_drifter_spec("unknown")
    with pytest.raises(ValueError, match="unknown Drifter ID"):
        create_drifter("unknown")


def test_runtime_catalog_and_engine_modules_do_not_scan_or_import_concrete_content():
    catalog_source = (ROOT / "src/app/content/catalog.py").read_text(encoding="utf-8")
    generated_source = OUTPUT_PATH.read_text(encoding="utf-8")

    for source in (catalog_source, generated_source):
        assert "pathlib" not in source
        assert "pkgutil" not in source
        assert "importlib" not in source
    for relative_path in (
        "src/app/combat/battle.py",
        "src/app/combat/resolver.py",
        "src/app/game/game_state.py",
        "src/app/game/overworld_session.py",
        "src/app/player/player_state.py",
    ):
        source = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "app.content.drifters." not in source
        assert "app.player.loadouts" not in source


def test_concrete_drifter_classes_and_split_authoring_paths_are_removed():
    for name in ("Brawler", "BlackMage", "RogueArcher", "Monk"):
        assert name not in character_module.__dict__
    for relative_path in (
        "src/app/player/loadouts/branoc.py",
        "src/app/player/loadouts/azhvielle.py",
        "src/app/player/loadouts/zhaivra.py",
        "src/app/player/loadouts/joruun.py",
        "src/app/world/character_profiles/branoc.py",
        "src/app/world/character_profiles/azhvielle.py",
        "src/app/world/character_profiles/zhaivra.py",
        "src/app/world/character_profiles/joruun.py",
    ):
        assert not (ROOT / relative_path).exists()


def test_drifter_spec_rejects_duplicate_moves_inventory_and_payload_ids():
    branoc = get_drifter_spec("branoc")
    zhaivra = get_drifter_spec("zhaivra")

    with pytest.raises(ValueError, match="unique names"):
        replace(branoc, combat_moves=(branoc.combat_moves[0],) * 2)
    with pytest.raises(ValueError, match="run-item IDs must be unique"):
        replace(
            zhaivra,
            starting_run_inventory=(
                (RunItemId.EMBER_SHARD, 1),
                (RunItemId.EMBER_SHARD, 1),
            ),
        )
    with pytest.raises(ValueError, match="prepared-payload IDs must be unique"):
        replace(
            zhaivra,
            starting_prepared_payloads=(
                (PreparedPayloadId.INFUSED_BARB, None),
                (PreparedPayloadId.INFUSED_BARB, None),
            ),
        )


def test_generator_rejects_mismatched_drifter_directory(tmp_path):
    path = tmp_path / "wrong" / "drifter.py"
    path.parent.mkdir()
    path.write_text(
        'DRIFTER = DrifterSpec(drifter_id="authored")\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="directory ID"):
        discover_drifter_ids(tmp_path)

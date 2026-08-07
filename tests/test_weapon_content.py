from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from app.content.catalog import (
    WEAPON_SPECS,
    _build_weapon_catalog,
    create_weapon,
    create_weapon_from_persistence_key,
    get_weapon_spec,
    get_weapon_spec_by_persistence_key,
)
from app.content.weapon_spec import WeaponSpec
from app.items.weapon import Weapon
from tools.generate_content_catalog import discover_weapon_ids


EXPECTED_WEAPONS = (
    {
        "item_id": "needle_of_plain_iron",
        "persistence_key": "NeedleOfPlainIron",
        "name": "Needle of Plain Iron",
        "weapon_type": "Ritual Needle",
        "intended_wielder": "Azhvielle",
        "stat_bonuses": {"intelligence": 3, "spirit": 1},
        "value": 2,
        "description": (
            "A long, unadorned iron needle used as both a weapon and a precise "
            "ritual focus."
        ),
    },
    {
        "item_id": "sathren",
        "persistence_key": "Sathren",
        "name": "Sathren",
        "weapon_type": "Alchemical Recurve Bow",
        "intended_wielder": "Zhaivra",
        "stat_bonuses": {"dexterity": 3, "intuition": 1},
        "value": 2,
        "description": (
            "A recurved bow grown from the bone-fiber of the Hollow Colossus "
            "and fitted with six alchemical reservoirs."
        ),
    },
    {
        "item_id": "sky_needle",
        "persistence_key": "SkyNeedle",
        "name": "Sky-Needle",
        "weapon_type": "Conductive Shakuj\u014d",
        "intended_wielder": "Joruun",
        "stat_bonuses": {"spirit": 2, "dexterity": 1, "intuition": 1},
        "value": 2,
        "description": (
            "An ash-wood shakuj\u014d fitted with copper collars and loose "
            "conductive rings."
        ),
    },
    {
        "item_id": "sunder_spire",
        "persistence_key": "SunderSpire",
        "name": "Sunder-Spire",
        "weapon_type": "Great Flamberge",
        "intended_wielder": "Branoc",
        "stat_bonuses": {"strength": 3, "constitution": 1},
        "value": 2,
        "description": (
            "A massive Deep-Iron flamberge forged from the broken weapons of "
            "Rhom-Ghal."
        ),
    },
)


def sample_spec(**overrides):
    values = {
        "item_id": "test_weapon",
        "persistence_key": "TestWeapon",
        "name": "Test Weapon",
        "weapon_type": "Test Type",
        "intended_wielder": "Tester",
        "stat_bonuses": {"strength": 1},
        "value": 0,
        "description": "Test description.",
    }
    values.update(overrides)
    return WeaponSpec(**values)


def test_all_signature_weapon_specs_match_the_independent_authored_contract():
    assert discover_weapon_ids() == tuple(
        expected["item_id"] for expected in EXPECTED_WEAPONS
    )
    assert tuple(spec.item_id for spec in WEAPON_SPECS) == discover_weapon_ids()

    for expected in EXPECTED_WEAPONS:
        spec = get_weapon_spec(expected["item_id"])
        weapon = create_weapon(expected["item_id"])

        for name in (
            "item_id",
            "persistence_key",
            "name",
            "weapon_type",
            "intended_wielder",
            "value",
            "description",
        ):
            assert getattr(spec, name) == expected[name]
            assert getattr(weapon, name) == expected[name]
        assert dict(spec.stat_bonuses) == expected["stat_bonuses"]
        assert weapon.stat_bonuses == expected["stat_bonuses"]
        assert sum(weapon.stat_bonuses.values()) == 4


def test_specs_catalogs_and_runtime_instances_are_immutable_or_fresh():
    spec = get_weapon_spec("sunder_spire")
    first = create_weapon("sunder_spire")
    second = create_weapon("sunder_spire")
    restored = create_weapon_from_persistence_key("SunderSpire")

    with pytest.raises(FrozenInstanceError):
        spec.name = "Changed"
    with pytest.raises(TypeError):
        spec.stat_bonuses["strength"] = 99
    with pytest.raises(TypeError):
        WEAPON_SPECS[0] = spec

    assert all(isinstance(weapon, Weapon) for weapon in (first, second, restored))
    assert first is not second and first is not restored and second is not restored
    assert first.stat_bonuses == second.stat_bonuses == restored.stat_bonuses

    exposed = first.stat_bonuses
    exposed["strength"] = 99
    assert second.stat_bonuses == {"strength": 3, "constitution": 1}


def test_catalog_uses_both_stable_identities_and_rejects_duplicates():
    for expected in EXPECTED_WEAPONS:
        assert (
            get_weapon_spec_by_persistence_key(expected["persistence_key"])
            is get_weapon_spec(expected["item_id"])
        )

    with pytest.raises(ValueError, match="unknown weapon item ID"):
        get_weapon_spec("unknown")
    with pytest.raises(ValueError, match="unknown weapon persistence key"):
        create_weapon_from_persistence_key("UnknownWeapon")
    with pytest.raises(ValueError, match="directory ID"):
        _build_weapon_catalog((("wrong_directory", sample_spec()),))

    spec = sample_spec()
    with pytest.raises(ValueError, match="duplicate weapon item ID"):
        _build_weapon_catalog(((spec.item_id, spec), (spec.item_id, spec)))
    second = sample_spec(item_id="other_weapon")
    with pytest.raises(ValueError, match="duplicate weapon persistence key"):
        _build_weapon_catalog(((spec.item_id, spec), (second.item_id, second)))


@pytest.mark.parametrize(
    "field,value,error",
    (
        ("item_id", "Bad Weapon", ValueError),
        ("item_id", "class", ValueError),
        ("item_id", None, TypeError),
        ("persistence_key", "", ValueError),
        ("name", "", ValueError),
        ("weapon_type", None, TypeError),
        ("intended_wielder", "", ValueError),
        ("stat_bonuses", None, TypeError),
        ("stat_bonuses", {"unknown": 1}, ValueError),
        ("stat_bonuses", {"strength": True}, TypeError),
        ("value", -1, ValueError),
        ("value", True, TypeError),
        ("description", None, TypeError),
    ),
)
def test_weapon_spec_rejects_invalid_authored_values(field, value, error):
    with pytest.raises(error):
        sample_spec(**{field: value})


def test_generator_rejects_weapon_directory_and_authored_id_mismatch(tmp_path):
    weapon_path = tmp_path / "wrong_directory" / "weapon.py"
    weapon_path.parent.mkdir()
    weapon_path.write_text(
        'WEAPON = WeaponSpec(item_id="authored_id")\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="directory ID"):
        discover_weapon_ids(tmp_path)


def test_runtime_weapon_catalog_contains_no_filesystem_discovery():
    source = Path("src/app/content/catalog.py").read_text(encoding="utf-8")

    assert "pathlib" not in source
    assert "pkgutil" not in source
    assert "importlib" not in source


def test_obsolete_signature_weapon_subclasses_are_removed():
    import app.items.weapon as weapon_module

    assert set(vars(weapon_module)).isdisjoint(
        {"SunderSpire", "SkyNeedle", "Sathren", "NeedleOfPlainIron"}
    )

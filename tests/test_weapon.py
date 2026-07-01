import pytest

from app.items.weapon import (
    NeedleOfPlainIron,
    Sathren,
    SkyNeedle,
    SunderSpire,
    Weapon,
)


EXPECTED_STARTING_WEAPONS = {
    SunderSpire: {
        "name": "Sunder-Spire",
        "weapon_type": "Great Flamberge",
        "intended_wielder": "Branoc",
        "stat_bonuses": {
            "strength": 3,
            "constitution": 1,
        },
        "value": 2,
        "description": "A massive Deep-Iron flamberge forged from the broken weapons of Rhom-Ghal.",
    },
    SkyNeedle: {
        "name": "Sky-Needle",
        "weapon_type": "Conductive Shakujō",
        "intended_wielder": "Joruun",
        "stat_bonuses": {
            "spirit": 2,
            "dexterity": 1,
            "intuition": 1,
        },
        "value": 2,
        "description": "An ash-wood shakujō fitted with copper collars and loose conductive rings.",
    },
    Sathren: {
        "name": "Sathren",
        "weapon_type": "Alchemical Recurve Bow",
        "intended_wielder": "Zhaivra",
        "stat_bonuses": {
            "dexterity": 3,
            "intuition": 1,
        },
        "value": 2,
        "description": (
            "A recurved bow grown from the bone-fiber of the Hollow Colossus "
            "and fitted with six alchemical reservoirs."
        ),
    },
    NeedleOfPlainIron: {
        "name": "Needle of Plain Iron",
        "weapon_type": "Ritual Needle",
        "intended_wielder": "Azhvielle",
        "stat_bonuses": {
            "intelligence": 3,
            "spirit": 1,
        },
        "value": 2,
        "description": "A long, unadorned iron needle used as both a weapon and a precise ritual focus.",
    },
}


def test_starting_weapons_have_exact_authored_data():
    for weapon_type, expected in EXPECTED_STARTING_WEAPONS.items():
        weapon = weapon_type()

        assert weapon.name == expected["name"]
        assert weapon.weapon_type == expected["weapon_type"]
        assert weapon.intended_wielder == expected["intended_wielder"]
        assert weapon.stat_bonuses == expected["stat_bonuses"]
        assert weapon.value == expected["value"]
        assert weapon.description == expected["description"]
        assert sum(weapon.stat_bonuses.values()) == 4


def test_weapon_validation_rejects_invalid_scalar_fields():
    valid_values = {
        "name": "test",
        "weapon_type": "test type",
        "intended_wielder": "test wielder",
        "stat_bonuses": {"strength": 1},
        "value": 0,
        "description": "",
    }

    for field_name in ("name", "weapon_type", "intended_wielder"):
        values = dict(valid_values)
        values[field_name] = ""
        with pytest.raises(ValueError):
            Weapon(**values)

        values = dict(valid_values)
        values[field_name] = None
        with pytest.raises(TypeError):
            Weapon(**values)

    with pytest.raises(TypeError):
        Weapon(**{**valid_values, "description": None})
    with pytest.raises(TypeError):
        Weapon(**{**valid_values, "value": True})
    with pytest.raises(TypeError):
        Weapon(**{**valid_values, "value": 1.5})
    with pytest.raises(ValueError):
        Weapon(**{**valid_values, "value": -1})


def test_weapon_validation_rejects_invalid_stat_bonuses():
    valid_values = {
        "name": "test",
        "weapon_type": "test type",
        "intended_wielder": "test wielder",
        "stat_bonuses": {"strength": 1},
        "value": 0,
        "description": "",
    }

    with pytest.raises(TypeError):
        Weapon(**{**valid_values, "stat_bonuses": None})
    with pytest.raises(ValueError):
        Weapon(**{**valid_values, "stat_bonuses": {"charisma": 1}})
    with pytest.raises(TypeError):
        Weapon(**{**valid_values, "stat_bonuses": {"strength": True}})
    with pytest.raises(TypeError):
        Weapon(**{**valid_values, "stat_bonuses": {"strength": 1.5}})
    with pytest.raises(ValueError):
        Weapon(**{**valid_values, "stat_bonuses": {"strength": -1}})


def test_weapon_stat_bonuses_are_defensively_owned():
    original_bonuses = {"strength": 1}
    weapon = Weapon(
        name="test",
        weapon_type="test type",
        intended_wielder="test wielder",
        stat_bonuses=original_bonuses,
        value=0,
        description="",
    )

    original_bonuses["strength"] = 99
    exposed_bonuses = weapon.stat_bonuses
    exposed_bonuses["strength"] = 42

    assert weapon.stat_bonuses == {"strength": 1}


def test_weapons_do_not_expose_legacy_combat_fields():
    weapon = SunderSpire()

    assert not hasattr(weapon, "attack")
    assert not hasattr(weapon, "defense")
    assert not hasattr(weapon, "magic_attack")
    assert not hasattr(weapon, "magic_defense")

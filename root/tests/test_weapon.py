import pytest

from app.content.catalog import create_weapon
from app.items.weapon import Weapon


def weapon_values(**overrides):
    values = {
        "item_id": "test_weapon",
        "persistence_key": "TestWeapon",
        "name": "test",
        "weapon_type": "test type",
        "intended_wielder": "test wielder",
        "stat_bonuses": {"strength": 1},
        "value": 0,
        "description": "",
    }
    values.update(overrides)
    return values


def test_weapon_validation_rejects_invalid_identity_and_scalar_fields():
    for item_id in ("", "Bad Weapon", "class"):
        with pytest.raises(ValueError):
            Weapon(**weapon_values(item_id=item_id))
    with pytest.raises(TypeError):
        Weapon(**weapon_values(item_id=None))

    for field_name in (
        "persistence_key",
        "name",
        "weapon_type",
        "intended_wielder",
    ):
        with pytest.raises(ValueError):
            Weapon(**weapon_values(**{field_name: ""}))
        with pytest.raises(TypeError):
            Weapon(**weapon_values(**{field_name: None}))

    with pytest.raises(TypeError):
        Weapon(**weapon_values(description=None))
    with pytest.raises(TypeError):
        Weapon(**weapon_values(value=True))
    with pytest.raises(TypeError):
        Weapon(**weapon_values(value=1.5))
    with pytest.raises(ValueError):
        Weapon(**weapon_values(value=-1))


def test_weapon_validation_rejects_invalid_stat_bonuses():
    with pytest.raises(TypeError):
        Weapon(**weapon_values(stat_bonuses=None))
    with pytest.raises(ValueError):
        Weapon(**weapon_values(stat_bonuses={"charisma": 1}))
    with pytest.raises(TypeError):
        Weapon(**weapon_values(stat_bonuses={"strength": True}))
    with pytest.raises(TypeError):
        Weapon(**weapon_values(stat_bonuses={"strength": 1.5}))
    with pytest.raises(ValueError):
        Weapon(**weapon_values(stat_bonuses={"strength": -1}))


def test_weapon_identity_is_read_only_and_bonuses_are_defensively_owned():
    original_bonuses = {"strength": 1}
    weapon = Weapon(**weapon_values(stat_bonuses=original_bonuses))

    original_bonuses["strength"] = 99
    exposed_bonuses = weapon.stat_bonuses
    exposed_bonuses["strength"] = 42

    assert weapon.item_id == "test_weapon"
    assert weapon.persistence_key == "TestWeapon"
    assert weapon.stat_bonuses == {"strength": 1}
    with pytest.raises(AttributeError):
        weapon.item_id = "changed"
    with pytest.raises(AttributeError):
        weapon.persistence_key = "Changed"


def test_weapons_do_not_expose_legacy_combat_fields():
    weapon = create_weapon("sunder_spire")

    assert not hasattr(weapon, "attack")
    assert not hasattr(weapon, "defense")
    assert not hasattr(weapon, "magic_attack")
    assert not hasattr(weapon, "magic_defense")

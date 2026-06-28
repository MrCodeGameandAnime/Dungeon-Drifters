import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.items.weapon import Staff
from app.player.character import BlackMage, Brawler
from app.player.player_state import PlayerState
from app.snapshot import validate_plain_value
from app.world.character_profiles.roster import get_profile_by_choice


class FakeWeaponShapedObject:
    attack = 1
    defense = 1
    magic_attack = 1
    magic_defense = 1
    value = 1


def assert_raises(error_type, action):
    try:
        action()
    except error_type as error:
        return error

    raise AssertionError(f"{error_type.__name__} was not raised")


def assert_strict_json(snapshot):
    validate_plain_value(snapshot)
    json.dumps(snapshot, allow_nan=False)


def test_default_player_snapshot_has_required_shape():
    player_state = PlayerState(Brawler())

    snapshot = player_state.snapshot()

    assert snapshot["identity"] == {
        "display_name": "Brawler",
        "full_display_name": "Brawler",
        "archetype_name": "Brawler",
        "profile": None,
    }
    assert snapshot["attributes"] == {
        "constitution": 14,
        "spirit": 6,
        "intelligence": 5,
        "strength": 15,
        "dexterity": 10,
        "intuition": 10,
    }
    assert "charisma" not in snapshot["attributes"]
    assert snapshot["resources"] == {
        "health": {"current": 60, "maximum": 60},
        "mana": {"current": 10, "maximum": 10},
    }
    assert snapshot["progression"] == {"level": 1, "exp": 0}
    assert "next_exp_threshold" not in snapshot["progression"]
    assert snapshot["gold"] == 0
    assert snapshot["inventory"] == []
    assert tuple(snapshot["equipment"].keys()) == PlayerState.EQUIPMENT_SLOTS
    assert all(item is None for item in snapshot["equipment"].values())
    assert len(snapshot["combat"]["moves"]) == 3
    assert snapshot["combat"]["class_mechanic"]["name"] == "Momentum"
    assert_strict_json(snapshot)


def test_profile_created_character_snapshot_uses_attached_profile_identity():
    profile = get_profile_by_choice("1")
    player_state = PlayerState(profile.create_character())

    snapshot = player_state.snapshot()

    assert snapshot["identity"]["display_name"] == "Ser Branoc"
    assert snapshot["identity"]["full_display_name"] == "Ser Branoc, the Unbroken Crest"
    assert snapshot["identity"]["archetype_name"] == "Brawler"
    assert snapshot["identity"]["profile"] == {
        "choice": "1",
        "short_name": "Ser Branoc",
        "display_name": "Ser Branoc, the Unbroken Crest",
    }
    assert_strict_json(snapshot)


def test_mutated_resources_progression_gold_and_inventory_are_reflected():
    player_state = PlayerState(BlackMage(), gold=15)
    player_state.health.take_damage(7)
    player_state.mana_resource.spend(8)
    player_state.character.level = 3
    player_state.character.exp = 25
    player_state.inventory.add_item("tonic")
    player_state.inventory.add_item("tonic")

    snapshot = player_state.snapshot()

    assert snapshot["resources"]["health"] == {"current": 23, "maximum": 30}
    assert snapshot["resources"]["mana"] == {"current": 62, "maximum": 70}
    assert snapshot["progression"] == {"level": 3, "exp": 25}
    assert snapshot["gold"] == 15
    assert snapshot["inventory"] == ["tonic", "tonic"]
    assert_strict_json(snapshot)


def test_supported_weapon_equipment_uses_explicit_plain_mapping():
    player_state = PlayerState(Brawler())
    staff = Staff()
    player_state.inventory.add_item(staff)

    player_state.equip("weapon", staff)
    snapshot = player_state.snapshot()

    assert snapshot["inventory"] == []
    assert snapshot["equipment"]["weapon"] == {
        "type": "Staff",
        "attack": 1,
        "defense": 1,
        "magic_attack": 3,
        "magic_defense": 2,
        "value": 3,
    }
    assert snapshot["equipment"]["off_hand"] is None
    assert_strict_json(snapshot)


def test_structured_moves_and_class_mechanic_are_plain_values():
    player_state = PlayerState(BlackMage())

    snapshot = player_state.snapshot()
    first_move = snapshot["combat"]["moves"][0]

    assert first_move == {
        "name": "fireball",
        "kind": "magic_damage",
        "mana_cost": 8,
        "power": 14,
        "scales_with": "intelligence",
        "accuracy": 88,
        "target": "enemy",
        "mechanic": "burn",
        "description": "A direct fire spell with a chance to leave burning damage later.",
    }
    assert snapshot["combat"]["class_mechanic"] == {
        "name": "Arcane Focus",
        "resource": "mana",
        "description": "Spells spend mana and scale primarily from intelligence.",
    }
    assert_strict_json(snapshot)


def test_snapshot_is_isolated_and_non_mutating():
    player_state = PlayerState(Brawler(), gold=10)
    player_state.inventory.add_item("tonic")
    health_before = player_state.health.current
    mana_before = player_state.mana_resource.current

    first_snapshot = player_state.snapshot()
    second_snapshot = player_state.snapshot()

    assert first_snapshot == second_snapshot
    first_snapshot["inventory"].append("changed")
    first_snapshot["equipment"]["weapon"] = "changed"
    first_snapshot["resources"]["health"]["current"] = 1

    assert player_state.inventory.items == ("tonic",)
    assert player_state.get_equipped("weapon") is None
    assert player_state.health.current == health_before
    assert player_state.mana_resource.current == mana_before

    player_state.health.take_damage(5)
    assert first_snapshot["resources"]["health"]["current"] == 1
    assert second_snapshot["resources"]["health"]["current"] == health_before
    assert player_state.snapshot()["resources"]["health"]["current"] == health_before - 5


def test_unsupported_inventory_and_equipment_values_fail_clearly():
    player_state = PlayerState(Brawler())
    player_state.inventory.add_item(object())

    inventory_error = assert_raises(TypeError, player_state.snapshot)
    assert "player.inventory[0]" in str(inventory_error)

    player_state = PlayerState(Brawler())
    item = object()
    player_state.inventory.add_item(item)
    player_state.equip("weapon", item)

    equipment_error = assert_raises(TypeError, player_state.snapshot)
    assert "player.equipment.weapon" in str(equipment_error)


def test_fake_weapon_shaped_object_is_not_serialized_as_weapon():
    player_state = PlayerState(Brawler())
    player_state.inventory.add_item(FakeWeaponShapedObject())

    inventory_error = assert_raises(TypeError, player_state.snapshot)
    assert "player.inventory[0]" in str(inventory_error)

    player_state = PlayerState(Brawler())
    item = FakeWeaponShapedObject()
    player_state.inventory.add_item(item)
    player_state.equip("weapon", item)

    equipment_error = assert_raises(TypeError, player_state.snapshot)
    assert "player.equipment.weapon" in str(equipment_error)


if __name__ == "__main__":
    test_default_player_snapshot_has_required_shape()
    test_profile_created_character_snapshot_uses_attached_profile_identity()
    test_mutated_resources_progression_gold_and_inventory_are_reflected()
    test_supported_weapon_equipment_uses_explicit_plain_mapping()
    test_structured_moves_and_class_mechanic_are_plain_values()
    test_snapshot_is_isolated_and_non_mutating()
    test_unsupported_inventory_and_equipment_values_fail_clearly()
    test_fake_weapon_shaped_object_is_not_serialized_as_weapon()
    print("Player snapshot test passed.")

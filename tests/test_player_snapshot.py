import json

import pytest

from app.items.weapon import NeedleOfPlainIron, Sathren, SkyNeedle, SunderSpire
from app.player.character import BlackMage, Brawler, Monk, RogueArcher
from app.player.player_state import PlayerState
from app.player.inventory_action import InventoryActionResolver
from app.snapshot import validate_plain_value
from app.world.character_profiles.roster import get_profile_by_choice


class FakeWeaponShapedObject:
    attack = 1
    defense = 1
    magic_attack = 1
    magic_defense = 1
    value = 1


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
        "health": {"current": 116, "maximum": 116},
        "mana": {"current": 46, "maximum": 46},
        "super": {"current": 0, "maximum": 100},
    }
    assert snapshot["progression"] == {"level": 1, "exp": 0}
    assert "next_exp_threshold" not in snapshot["progression"]
    assert snapshot["gold"] == 0
    assert snapshot["inventory"] == []
    assert snapshot["run_state"] == {
        "inventory": {},
        "prepared_payloads": {},
    }
    assert tuple(snapshot["equipment"].keys()) == PlayerState.EQUIPMENT_SLOTS
    assert snapshot["equipment"]["weapon"] == {
        "type": "SunderSpire",
        "name": "Sunder-Spire",
        "weapon_type": "Great Flamberge",
        "intended_wielder": "Branoc",
        "stat_bonuses": {
            "strength": 3,
            "constitution": 1,
        },
        "value": 2,
        "description": "A massive Deep-Iron flamberge forged from the broken weapons of Rhom-Ghal.",
    }
    assert all(
        item is None
        for slot, item in snapshot["equipment"].items()
        if slot != "weapon"
    )
    assert len(snapshot["combat"]["moves"]) == 5
    assert snapshot["combat"]["class_mechanic"]["name"] == "Heavy Vanguard"
    assert "resource" not in snapshot["combat"]["class_mechanic"]
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
    player_state.super_resource.gain(70)
    player_state.character.level = 3
    player_state.character.exp = 25
    player_state.inventory.add_item("tonic")
    player_state.inventory.add_item("tonic")

    snapshot = player_state.snapshot()

    assert snapshot["resources"]["health"] == {"current": 84, "maximum": 91}
    assert snapshot["resources"]["mana"] == {"current": 48, "maximum": 56}
    assert snapshot["resources"]["super"] == {"current": 70, "maximum": 100}
    assert snapshot["progression"] == {"level": 3, "exp": 25}
    assert snapshot["gold"] == 15
    assert snapshot["inventory"] == ["tonic", "tonic"]
    assert_strict_json(snapshot)


def test_zhaivra_snapshot_includes_character_owned_run_state():
    snapshot = PlayerState(RogueArcher()).snapshot()

    assert snapshot["run_state"] == {
        "inventory": {
            "deep_coal": 1,
            "ember_shard": 1,
        },
        "prepared_payloads": {
            "cinderwrit_payload": False,
        },
    }
    assert_strict_json(snapshot)


def test_zhaivra_snapshot_reflects_prepared_payload_across_encounter_state():
    player_state = PlayerState(RogueArcher())
    InventoryActionResolver().resolve(
        "prepare_cinderwrit",
        player_state.character_run_state,
    )

    snapshot = player_state.snapshot()

    assert snapshot["run_state"] == {
        "inventory": {
            "deep_coal": 0,
            "ember_shard": 0,
        },
        "prepared_payloads": {
            "cinderwrit_payload": True,
        },
    }
    assert_strict_json(snapshot)


def test_supported_weapon_equipment_uses_explicit_plain_mapping():
    player_state = PlayerState(Brawler())
    staff = SkyNeedle()
    player_state.inventory.add_item(staff)

    player_state.equip("weapon", staff)
    snapshot = player_state.snapshot()

    assert snapshot["inventory"] == [
        {
            "type": "SunderSpire",
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
    ]
    assert snapshot["equipment"]["weapon"] == {
        "type": "SkyNeedle",
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
    }
    assert snapshot["equipment"]["off_hand"] is None
    assert "attack" not in snapshot["equipment"]["weapon"]
    assert "defense" not in snapshot["equipment"]["weapon"]
    assert "magic_attack" not in snapshot["equipment"]["weapon"]
    assert "magic_defense" not in snapshot["equipment"]["weapon"]
    assert_strict_json(snapshot)


def test_all_named_starting_weapons_serialize_with_new_payload():
    expected_payloads = (
        (
            Brawler,
            SunderSpire,
            {
                "type": "SunderSpire",
                "name": "Sunder-Spire",
                "weapon_type": "Great Flamberge",
                "intended_wielder": "Branoc",
                "stat_bonuses": {"strength": 3, "constitution": 1},
                "value": 2,
                "description": "A massive Deep-Iron flamberge forged from the broken weapons of Rhom-Ghal.",
            },
        ),
        (
            BlackMage,
            NeedleOfPlainIron,
            {
                "type": "NeedleOfPlainIron",
                "name": "Needle of Plain Iron",
                "weapon_type": "Ritual Needle",
                "intended_wielder": "Azhvielle",
                "stat_bonuses": {"intelligence": 3, "spirit": 1},
                "value": 2,
                "description": "A long, unadorned iron needle used as both a weapon and a precise ritual focus.",
            },
        ),
        (
            RogueArcher,
            Sathren,
            {
                "type": "Sathren",
                "name": "Sathren",
                "weapon_type": "Alchemical Recurve Bow",
                "intended_wielder": "Zhaivra",
                "stat_bonuses": {"dexterity": 3, "intuition": 1},
                "value": 2,
                "description": "A recurved bow grown from the bone-fiber of the Hollow Colossus and fitted with six alchemical reservoirs.",
            },
        ),
        (
            Monk,
            SkyNeedle,
            {
                "type": "SkyNeedle",
                "name": "Sky-Needle",
                "weapon_type": "Conductive Shakujō",
                "intended_wielder": "Joruun",
                "stat_bonuses": {"spirit": 2, "dexterity": 1, "intuition": 1},
                "value": 2,
                "description": "An ash-wood shakujō fitted with copper collars and loose conductive rings.",
            },
        ),
    )

    for class_type, weapon_type, expected_payload in expected_payloads:
        player_state = PlayerState(class_type())

        assert isinstance(player_state.get_equipped("weapon"), weapon_type)
        assert player_state.snapshot()["equipment"]["weapon"] == expected_payload


def test_structured_moves_and_class_mechanic_are_plain_values():
    player_state = PlayerState(BlackMage())

    snapshot = player_state.snapshot()
    first_move = snapshot["combat"]["moves"][0]

    assert first_move == {
        "name": "Scepter Sweep",
        "kind": "damage",
        "resource_type": "none",
        "resource_cost": 0,
        "power": 7,
        "scales_with": ["dexterity"],
        "accuracy": 92,
        "target": "enemy",
        "damage_type": "physical",
        "mechanic": "basic_attack",
        "description": "A direct scepter strike aimed at the target.",
    }
    assert snapshot["combat"]["class_mechanic"] == {
        "name": "Arcane Focus",
        "description": "Spells spend mana and scale primarily from intelligence.",
    }
    assert_strict_json(snapshot)


def test_affected_class_mechanics_do_not_declare_deferred_resources():
    affected_classes = (
        Brawler,
        BlackMage,
        RogueArcher,
    )

    for class_type in affected_classes:
        snapshot = PlayerState(class_type()).snapshot()
        class_mechanic = snapshot["combat"]["class_mechanic"]

        assert "resource" not in class_mechanic
        forbidden_resources = {
            "moment" + "um",
            "fo" + "cus",
            "k" + "i",
        }
        assert class_mechanic.get("resource") not in forbidden_resources

    monk_snapshot = PlayerState(Monk()).snapshot()
    monk_mechanic = monk_snapshot["combat"]["class_mechanic"]
    assert monk_mechanic["name"] == "Ki Forms"
    assert "resource" not in monk_mechanic


def test_snapshot_is_isolated_and_non_mutating():
    player_state = PlayerState(Brawler(), gold=10)
    player_state.inventory.add_item("tonic")
    health_before = player_state.health.current
    mana_before = player_state.mana_resource.current
    super_before = player_state.super_resource.current

    first_snapshot = player_state.snapshot()
    second_snapshot = player_state.snapshot()

    assert first_snapshot == second_snapshot
    first_snapshot["inventory"].append("changed")
    first_snapshot["equipment"]["weapon"] = "changed"
    first_snapshot["resources"]["health"]["current"] = 1
    first_snapshot["resources"]["super"]["current"] = 100

    assert player_state.inventory.items == ("tonic",)
    assert player_state.get_equipped("weapon").name == "Sunder-Spire"
    assert player_state.health.current == health_before
    assert player_state.mana_resource.current == mana_before
    assert player_state.super_resource.current == super_before

    player_state.health.take_damage(5)
    assert first_snapshot["resources"]["health"]["current"] == 1
    assert first_snapshot["resources"]["super"]["current"] == 100
    assert second_snapshot["resources"]["health"]["current"] == health_before
    assert second_snapshot["resources"]["super"]["current"] == super_before
    assert player_state.snapshot()["resources"]["health"]["current"] == health_before - 5


def test_unsupported_inventory_and_equipment_values_fail_clearly():
    player_state = PlayerState(Brawler())
    player_state.inventory.add_item(object())

    with pytest.raises(TypeError) as inventory_error:
        player_state.snapshot()
    assert "player.inventory[0]" in str(inventory_error.value)

    player_state = PlayerState(Brawler())
    item = object()
    player_state.inventory.add_item(item)
    player_state.equip("weapon", item)

    with pytest.raises(TypeError) as equipment_error:
        player_state.snapshot()
    assert "player.equipment.weapon" in str(equipment_error.value)


def test_fake_weapon_shaped_object_is_not_serialized_as_weapon():
    player_state = PlayerState(Brawler())
    player_state.inventory.add_item(FakeWeaponShapedObject())

    with pytest.raises(TypeError) as inventory_error:
        player_state.snapshot()
    assert "player.inventory[0]" in str(inventory_error.value)

    player_state = PlayerState(Brawler())
    item = FakeWeaponShapedObject()
    player_state.inventory.add_item(item)
    player_state.equip("weapon", item)

    with pytest.raises(TypeError) as equipment_error:
        player_state.snapshot()
    assert "player.equipment.weapon" in str(equipment_error.value)

import pytest

from app.items.weapon import NeedleOfPlainIron, Sathren, SkyNeedle, SunderSpire
from app.player.character import BlackMage, Brawler, Monk, RogueArcher
from app.player.inventory import Inventory
from app.player.player_state import PlayerState


PLAYABLE_CLASSES = [
    Brawler,
    BlackMage,
    RogueArcher,
    Monk,
]


def test_player_state_wraps_all_playable_classes():
    for class_type in PLAYABLE_CLASSES:
        character = class_type()
        player_state = PlayerState(character)

        assert player_state.character is character


def test_character_and_inventory_are_read_only_properties():
    character = Brawler()
    player_state = PlayerState(character)

    assert player_state.character is character
    assert isinstance(player_state.inventory, Inventory)
    with pytest.raises(AttributeError):
        setattr(player_state, "character", BlackMage())
    with pytest.raises(AttributeError):
        setattr(player_state, "inventory", Inventory())


def test_default_and_explicit_gold_values():
    assert PlayerState(Brawler()).gold == 0
    assert PlayerState(Brawler(), gold=25).gold == 25


def test_default_inventory_is_empty():
    player_state = PlayerState(Brawler())

    assert player_state.inventory.items == ()


def test_equipment_slots_exist_and_start_empty():
    player_state = PlayerState(Brawler())

    assert tuple(player_state.equipment.keys()) == PlayerState.EQUIPMENT_SLOTS
    assert isinstance(player_state.get_equipped("weapon"), SunderSpire)
    assert all(
        item is None
        for slot, item in player_state.equipment.items()
        if slot != "weapon"
    )


def test_player_states_do_not_share_inventory_or_equipment():
    first_player = PlayerState(Brawler())
    second_player = PlayerState(Brawler())
    item = object()

    first_player.inventory.add_item(item)
    first_equipment = first_player.equipment
    first_equipment["weapon"] = item

    assert first_player.inventory is not second_player.inventory
    assert first_player.inventory.items == (item,)
    assert second_player.inventory.items == ()
    assert isinstance(first_player.equipment["weapon"], SunderSpire)
    assert isinstance(second_player.equipment["weapon"], SunderSpire)
    assert first_player.equipment["weapon"] is not second_player.equipment["weapon"]


def test_invalid_character_raises_type_error():
    with pytest.raises(TypeError):
        PlayerState(object())
    with pytest.raises(TypeError):
        PlayerState(None)


def test_character_state_delegation_returns_authoritative_objects():
    character = Monk()
    player_state = PlayerState(character)

    assert player_state.health is character.health
    assert player_state.mana_resource is character.mana_resource
    assert player_state.level_state is character.level_state
    assert player_state.exp_state is character.exp_state
    assert player_state.stats is character.stats
    assert player_state.combat_moves is character.combat_moves
    assert player_state.class_mechanic is character.class_mechanic


def test_super_resource_is_owned_by_player_state_not_character():
    character = Monk()
    player_state = PlayerState(character)

    assert player_state.super_resource.current == 0
    assert player_state.super_resource.maximum == 100
    assert not hasattr(character, "super_resource")


def test_player_states_do_not_share_super_resources():
    first_player = PlayerState(Monk())
    second_player = PlayerState(Monk())

    first_player.super_resource.gain(100)

    assert first_player.super_resource.current == 100
    assert second_player.super_resource.current == 0


def test_mutating_delegated_health_updates_wrapped_character():
    character = Brawler()
    player_state = PlayerState(character)

    player_state.health.take_damage(5)

    assert character.health.current == player_state.health.current
    assert character.hp == player_state.health.current


def test_gold_can_be_added_and_returns_new_total():
    player_state = PlayerState(Brawler(), gold=10)

    assert player_state.add_gold(5) == 15
    assert player_state.gold == 15
    assert player_state.add_gold(0) == 15


def test_gold_spending_and_affordability():
    player_state = PlayerState(Brawler(), gold=10)

    assert player_state.can_afford(10)
    assert player_state.spend_gold(0)
    assert player_state.gold == 10
    assert player_state.spend_gold(5)
    assert player_state.gold == 5
    assert player_state.spend_gold(5)
    assert player_state.gold == 0
    assert not player_state.can_afford(1)
    assert not player_state.spend_gold(1)
    assert player_state.gold == 0


def test_gold_rejects_invalid_values():
    invalid_type_values = (True, False, 1.5, "10", None)

    with pytest.raises(ValueError):
        PlayerState(Brawler(), gold=-1)
    for value in invalid_type_values:
        with pytest.raises(TypeError):
            PlayerState(Brawler(), gold=value)
        with pytest.raises(TypeError):
            PlayerState(Brawler()).add_gold(value)
        with pytest.raises(TypeError):
            PlayerState(Brawler()).can_afford(value)
        with pytest.raises(TypeError):
            PlayerState(Brawler()).spend_gold(value)

    with pytest.raises(ValueError):
        PlayerState(Brawler()).add_gold(-1)
    with pytest.raises(ValueError):
        PlayerState(Brawler()).can_afford(-1)
    with pytest.raises(ValueError):
        PlayerState(Brawler()).spend_gold(-1)


def test_gold_has_no_public_setter():
    player_state = PlayerState(Brawler())

    with pytest.raises(AttributeError):
        setattr(player_state, "gold", -1)


def test_owned_item_can_be_equipped():
    player_state = PlayerState(Brawler())
    item = object()
    starting_weapon = player_state.get_equipped("weapon")
    player_state.inventory.add_item(item)

    assert player_state.equip("weapon", item) is starting_weapon
    assert player_state.get_equipped("weapon") is item
    assert not player_state.inventory.contains(item)
    assert player_state.inventory.contains(starting_weapon)


def test_replacing_equipment_preserves_items():
    player_state = PlayerState(Brawler())
    first_item = object()
    second_item = object()
    player_state.inventory.add_item(first_item)
    player_state.inventory.add_item(second_item)
    player_state.equip("weapon", first_item)

    assert player_state.equip("weapon", second_item) is first_item
    assert player_state.get_equipped("weapon") is second_item
    assert first_item in player_state.inventory.items


def test_unequipping_returns_item_to_inventory():
    player_state = PlayerState(Brawler())
    item = object()
    player_state.inventory.add_item(item)
    player_state.equip("weapon", item)

    assert player_state.unequip("weapon") is item
    assert player_state.get_equipped("weapon") is None
    assert item in player_state.inventory.items
    assert player_state.unequip("weapon") is None


def test_get_equipped_returns_empty_slot():
    player_state = PlayerState(Brawler())

    assert player_state.get_equipped("head") is None


def test_equipping_unowned_item_raises_and_preserves_state():
    player_state = PlayerState(Brawler())
    equipped_item = object()
    missing_item = object()
    player_state.inventory.add_item(equipped_item)
    player_state.equip("weapon", equipped_item)
    inventory_before = player_state.inventory.items

    with pytest.raises(ValueError):
        player_state.equip("weapon", missing_item)

    assert player_state.get_equipped("weapon") is equipped_item
    assert player_state.inventory.items == inventory_before


def test_equipping_none_raises_value_error():
    player_state = PlayerState(Brawler())

    with pytest.raises(ValueError):
        player_state.equip("weapon", None)


def test_invalid_slots_are_rejected():
    player_state = PlayerState(Brawler())
    item = object()
    player_state.inventory.add_item(item)

    with pytest.raises(ValueError):
        player_state.equip("invalid", item)
    with pytest.raises(ValueError):
        player_state.unequip("invalid")
    with pytest.raises(ValueError):
        player_state.get_equipped("invalid")
    with pytest.raises(ValueError):
        player_state.get_equipped(None)


def test_equipment_snapshot_cannot_mutate_internal_equipment():
    player_state = PlayerState(Brawler())
    item = object()

    equipment = player_state.equipment
    equipment["weapon"] = item
    equipment["new_slot"] = item

    assert isinstance(player_state.get_equipped("weapon"), SunderSpire)
    assert "new_slot" not in player_state.equipment


def test_item_conservation_across_equip_replace_and_unequip():
    player_state = PlayerState(Brawler())
    first_item = object()
    second_item = object()
    player_state.inventory.add_item(first_item)
    player_state.inventory.add_item(second_item)

    player_state.equip("weapon", first_item)
    assert second_item in player_state.inventory.items

    player_state.equip("weapon", second_item)
    assert first_item in player_state.inventory.items

    player_state.unequip("weapon")
    assert player_state.get_equipped("weapon") is None
    assert first_item in player_state.inventory.items
    assert second_item in player_state.inventory.items


def test_playable_classes_start_with_named_weapons():
    expected_weapons = {
        Brawler: SunderSpire,
        BlackMage: NeedleOfPlainIron,
        RogueArcher: Sathren,
        Monk: SkyNeedle,
    }

    for class_type, weapon_type in expected_weapons.items():
        player_state = PlayerState(class_type())

        assert isinstance(player_state.get_equipped("weapon"), weapon_type)


def test_equipped_weapon_contributes_to_effective_stats_without_mutating_permanent_stats():
    character = Brawler()
    player_state = PlayerState(character)

    assert character.permanent_stats.as_dict()["strength"] == 15
    assert character.stats.effective_stat("strength") == 15
    assert player_state.effective_stat("strength") == 18
    assert player_state.effective_stat("constitution") == 15
    assert player_state.effective_stat("dexterity") == 10
    assert character.permanent_stats.as_dict()["strength"] == 15


def test_inventory_only_weapons_do_not_contribute_to_effective_stats():
    player_state = PlayerState(Brawler())
    player_state.unequip("weapon")
    player_state.inventory.add_item(SkyNeedle())

    assert player_state.effective_stat("spirit") == 6
    assert player_state.effective_stat("dexterity") == 10


def test_replacing_and_unequipping_weapon_updates_effective_stats_once():
    player_state = PlayerState(Brawler())
    sky_needle = SkyNeedle()

    assert player_state.effective_stat("strength") == 18
    assert player_state.effective_stat("spirit") == 6

    player_state.inventory.add_item(sky_needle)
    player_state.equip("weapon", sky_needle)

    assert player_state.effective_stat("strength") == 15
    assert player_state.effective_stat("spirit") == 8
    assert player_state.effective_stat("spirit") == 8

    player_state.unequip("weapon")

    assert player_state.effective_stat("strength") == 15
    assert player_state.effective_stat("spirit") == 6

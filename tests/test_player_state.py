import pytest

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
    assert all(item is None for item in player_state.equipment.values())


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
    assert first_player.equipment["weapon"] is None
    assert second_player.equipment["weapon"] is None


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
    player_state.inventory.add_item(item)

    assert player_state.equip("weapon", item) is None
    assert player_state.get_equipped("weapon") is item
    assert not player_state.inventory.contains(item)


def test_replacing_equipment_preserves_items():
    player_state = PlayerState(Brawler())
    first_item = object()
    second_item = object()
    player_state.inventory.add_item(first_item)
    player_state.inventory.add_item(second_item)
    player_state.equip("weapon", first_item)

    assert player_state.equip("weapon", second_item) is first_item
    assert player_state.get_equipped("weapon") is second_item
    assert player_state.inventory.items == (first_item,)


def test_unequipping_returns_item_to_inventory():
    player_state = PlayerState(Brawler())
    item = object()
    player_state.inventory.add_item(item)
    player_state.equip("weapon", item)

    assert player_state.unequip("weapon") is item
    assert player_state.get_equipped("weapon") is None
    assert player_state.inventory.items == (item,)
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

    assert player_state.get_equipped("weapon") is None
    assert "new_slot" not in player_state.equipment


def test_item_conservation_across_equip_replace_and_unequip():
    player_state = PlayerState(Brawler())
    first_item = object()
    second_item = object()
    player_state.inventory.add_item(first_item)
    player_state.inventory.add_item(second_item)

    player_state.equip("weapon", first_item)
    assert player_state.inventory.items == (second_item,)

    player_state.equip("weapon", second_item)
    assert player_state.inventory.items == (first_item,)

    player_state.unequip("weapon")
    assert player_state.get_equipped("weapon") is None
    assert player_state.inventory.items == (first_item, second_item)

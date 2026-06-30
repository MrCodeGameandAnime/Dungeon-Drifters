from app.player.inventory import Inventory


class MatchingItem:
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return isinstance(other, MatchingItem) and self.value == other.value


def test_new_inventory_starts_empty():
    inventory = Inventory()

    assert inventory.items == ()


def test_items_returns_immutable_snapshot():
    inventory = Inventory()
    item = object()

    inventory.add_item(item)
    snapshot = inventory.items

    assert isinstance(snapshot, tuple)
    assert snapshot == (item,)


def test_adding_item_works_and_returns_none():
    inventory = Inventory()
    item = object()

    result = inventory.add_item(item)

    assert result is None
    assert inventory.items == (item,)


def test_contains_reports_accurately():
    inventory = Inventory()
    item = object()
    missing_item = object()

    inventory.add_item(item)

    assert inventory.contains(item)
    assert not inventory.contains(missing_item)


def test_removing_existing_item_returns_true():
    inventory = Inventory()
    item = object()
    inventory.add_item(item)

    assert inventory.remove_item(item)
    assert inventory.items == ()


def test_removing_missing_item_returns_false():
    inventory = Inventory()

    assert not inventory.remove_item(object())
    assert inventory.items == ()


def test_duplicate_items_are_allowed():
    inventory = Inventory()
    item = object()

    inventory.add_item(item)
    inventory.add_item(item)

    assert inventory.items == (item, item)


def test_removing_one_duplicate_leaves_the_other():
    inventory = Inventory()
    item = object()

    inventory.add_item(item)
    inventory.add_item(item)

    assert inventory.remove_item(item)
    assert inventory.items == (item,)


def test_removal_uses_first_match_behavior():
    inventory = Inventory()
    first_item = MatchingItem("gem")
    second_item = MatchingItem("gem")

    inventory.add_item(first_item)
    inventory.add_item(second_item)

    assert inventory.remove_item(MatchingItem("gem"))
    assert inventory.items == (second_item,)
    assert inventory.items[0] is second_item


def test_snapshot_cannot_mutate_internal_inventory():
    inventory = Inventory()
    item = object()
    inventory.add_item(item)
    snapshot = inventory.items

    snapshot += (object(),)

    assert inventory.items == (item,)


def test_inventory_instances_do_not_share_item_collections():
    first_inventory = Inventory()
    second_inventory = Inventory()
    item = object()

    first_inventory.add_item(item)

    assert first_inventory.items == (item,)
    assert second_inventory.items == ()


def test_inventory_accepts_arbitrary_item_objects():
    inventory = Inventory()
    item = {"name": "strange charm"}

    inventory.add_item(item)

    assert inventory.contains(item)

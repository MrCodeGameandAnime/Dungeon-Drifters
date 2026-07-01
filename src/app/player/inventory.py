"""Player inventory state."""


class Inventory:
    def __init__(self):
        self._items = []

    @property
    def items(self):
        return tuple(self._items)

    def add_item(self, item):
        self._items.append(item)

    def remove_item(self, item):
        for index, owned_item in enumerate(self._items):
            if owned_item == item:
                del self._items[index]
                return True

        return False

    def contains(self, item):
        return any(owned_item == item for owned_item in self._items)

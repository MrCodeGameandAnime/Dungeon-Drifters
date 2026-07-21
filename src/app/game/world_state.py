"""Persistent world state for one active game session."""

from app.snapshot import to_plain_value


class WorldState:
    def __init__(self):
        self._discovered_locations = []
        self._defeated_encounters = []
        self._opened_objects = []
        self._consumed_objects = []
        self._dungeon_changes = {}

    @property
    def discovered_locations(self):
        return tuple(self._discovered_locations)

    @property
    def defeated_encounters(self):
        return tuple(self._defeated_encounters)

    @property
    def opened_objects(self):
        return tuple(self._opened_objects)

    @property
    def consumed_objects(self):
        return tuple(self._consumed_objects)

    @property
    def dungeon_changes(self):
        return dict(self._dungeon_changes)

    def discover_location(self, location):
        if location not in self._discovered_locations:
            self._discovered_locations.append(location)

    def mark_encounter_defeated(self, encounter):
        if encounter not in self._defeated_encounters:
            self._defeated_encounters.append(encounter)

    def mark_object_opened(self, world_object):
        if world_object not in self._opened_objects:
            self._opened_objects.append(world_object)

    def mark_object_consumed(self, world_object):
        if world_object not in self._consumed_objects:
            self._consumed_objects.append(world_object)

    def set_dungeon_change(self, key, value):
        self._dungeon_changes[key] = value

    @classmethod
    def from_snapshot(cls, snapshot):
        state = cls()
        state._discovered_locations = list(snapshot["discovered_locations"])
        state._defeated_encounters = list(snapshot["defeated_encounters"])
        state._opened_objects = list(snapshot["opened_objects"])
        state._consumed_objects = list(snapshot["consumed_objects"])
        state._dungeon_changes = dict(snapshot["dungeon_changes"])
        return state

    def snapshot(self):
        return to_plain_value(
            {
                "discovered_locations": list(self.discovered_locations),
                "defeated_encounters": list(self.defeated_encounters),
                "opened_objects": list(self.opened_objects),
                "consumed_objects": list(self.consumed_objects),
                "dungeon_changes": self.dungeon_changes,
            },
            "world",
        )

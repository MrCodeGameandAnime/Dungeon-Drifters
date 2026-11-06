"""Persistent world state for one active game session."""

from app.snapshot import to_plain_value


class WorldState:
    def __init__(self):
        self._discovered_locations = []
        self._defeated_encounters = []
        self._opened_objects = []
        self._consumed_objects = []
        self._permanent_discovery_claims = []
        self._discovered_permanent_discovery_sources = []
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
    def permanent_discovery_claims(self):
        return tuple(self._permanent_discovery_claims)

    @property
    def discovered_permanent_discovery_sources(self):
        return tuple(self._discovered_permanent_discovery_sources)

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

    def claim_permanent_discovery(self, source_id):
        self.discover_permanent_discovery_source(source_id)
        if source_id not in self._permanent_discovery_claims:
            self._permanent_discovery_claims.append(source_id)

    def discover_permanent_discovery_source(self, source_id):
        if not isinstance(source_id, str) or not source_id:
            raise ValueError("discovery source ID must be a non-empty string")
        if source_id not in self._discovered_permanent_discovery_sources:
            self._discovered_permanent_discovery_sources.append(source_id)

    def set_dungeon_change(self, key, value):
        self._dungeon_changes[key] = value

    @classmethod
    def from_snapshot(cls, snapshot):
        state = cls()
        state._discovered_locations = list(snapshot["discovered_locations"])
        state._defeated_encounters = list(snapshot["defeated_encounters"])
        state._opened_objects = list(snapshot["opened_objects"])
        state._consumed_objects = list(snapshot["consumed_objects"])
        state._permanent_discovery_claims = list(
            snapshot.get("permanent_discovery_claims", ())
        )
        state._discovered_permanent_discovery_sources = list(
            snapshot.get("discovered_permanent_discovery_sources", ())
        )
        state._dungeon_changes = dict(snapshot["dungeon_changes"])
        return state

    def snapshot(self):
        return to_plain_value(
            {
                "discovered_locations": list(self.discovered_locations),
                "defeated_encounters": list(self.defeated_encounters),
                "opened_objects": list(self.opened_objects),
                "consumed_objects": list(self.consumed_objects),
                "permanent_discovery_claims": list(
                    self.permanent_discovery_claims
                ),
                "discovered_permanent_discovery_sources": list(
                    self.discovered_permanent_discovery_sources
                ),
                "dungeon_changes": self.dungeon_changes,
            },
            "world",
        )

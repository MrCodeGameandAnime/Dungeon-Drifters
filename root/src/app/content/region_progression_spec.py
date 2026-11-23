"""Finite authored region and destination identities for M8 progression."""

from dataclasses import dataclass

from app.content.route_spec import validate_content_id


@dataclass(frozen=True)
class RegionSpec:
    region_id: str
    display_name: str
    destination_ids: tuple[str, ...]

    def __post_init__(self):
        object.__setattr__(
            self,
            "region_id",
            validate_content_id("region_id", self.region_id),
        )
        if not isinstance(self.display_name, str) or not self.display_name.strip():
            raise ValueError("display_name must not be empty")
        if not isinstance(self.destination_ids, tuple):
            raise TypeError("destination_ids must be a tuple")
        if any(
            not isinstance(destination_id, str) or not destination_id
            for destination_id in self.destination_ids
        ):
            raise ValueError("destination_ids must contain nonempty IDs")


@dataclass(frozen=True)
class DestinationSpec:
    destination_id: str
    display_name: str
    region_id: str
    route_id: str
    required_floor_clear: str | None = None
    knowledge_fact_id: str | None = None
    requires_tutorial: bool = False
    requires_full_roster: bool = False
    portal_visible: bool = True

    def __post_init__(self):
        for field in ("destination_id", "region_id", "route_id"):
            object.__setattr__(
                self,
                field,
                validate_content_id(field, getattr(self, field)),
            )
        if not isinstance(self.display_name, str) or not self.display_name.strip():
            raise ValueError("display_name must not be empty")
        if self.required_floor_clear is not None:
            object.__setattr__(
                self,
                "required_floor_clear",
                validate_content_id(
                    "required_floor_clear",
                    self.required_floor_clear,
                ),
            )
        if self.knowledge_fact_id is not None:
            object.__setattr__(
                self,
                "knowledge_fact_id",
                validate_content_id("knowledge_fact_id", self.knowledge_fact_id),
            )
        for field in ("requires_tutorial", "requires_full_roster", "portal_visible"):
            if not isinstance(getattr(self, field), bool):
                raise TypeError(f"{field} must be a boolean")


REGION_SPECS = (
    RegionSpec(
        "region_1",
        "Region 1",
        (
            "surface",
            "floor_one",
            "floor_two",
            "floor_three",
            "drowned_reliquary",
            "ashen_vault",
        ),
    ),
    RegionSpec("region_2", "Region 2", ()),
)

M8_KNOWLEDGE_FACT_IDS = (
    "m8_fact_drowned_reliquary",
    "m8_fact_reliquary_threats",
    "m8_fact_ashen_vault",
    "m8_fact_ashen_regent",
)
M8_KNOWLEDGE_FACT_LABELS = (
    ("m8_fact_drowned_reliquary", "Drowned Reliquary"),
    ("m8_fact_reliquary_threats", "Reliquary threats"),
    ("m8_fact_ashen_vault", "Ashen Vault"),
    ("m8_fact_ashen_regent", "Ashen Regent"),
)

DESTINATION_SPECS = (
    DestinationSpec(
        "surface",
        "Surface",
        "region_1",
        "surface",
        portal_visible=False,
    ),
    DestinationSpec(
        "floor_one",
        "Floor I",
        "region_1",
        "floor_one",
        requires_tutorial=True,
    ),
    DestinationSpec(
        "floor_two",
        "Floor II",
        "region_1",
        "floor_two",
        required_floor_clear="floor_one",
    ),
    DestinationSpec(
        "floor_three",
        "Floor III",
        "region_1",
        "floor_three",
        required_floor_clear="floor_two",
        requires_full_roster=True,
    ),
    DestinationSpec(
        "drowned_reliquary",
        "Drowned Reliquary",
        "region_1",
        "floor_four",
        required_floor_clear="floor_three",
        knowledge_fact_id="m8_fact_drowned_reliquary",
        requires_full_roster=True,
    ),
    DestinationSpec(
        "ashen_vault",
        "Ashen Vault",
        "region_1",
        "floor_five_approach",
        required_floor_clear="floor_four",
        knowledge_fact_id="m8_fact_ashen_vault",
    ),
)

M8_DROWNED_BRIEFING_EVENT_ID = "m8_drowned_reliquary_briefing"
M8_ASHEN_ARENA_REVEALED_EVENT_ID = "m8_ashen_arena_revealed"


def get_region_spec(region_id):
    for spec in REGION_SPECS:
        if spec.region_id == region_id:
            return spec
    raise ValueError(f"unknown region ID: {region_id}")


def get_destination_spec(destination_id):
    for spec in DESTINATION_SPECS:
        if spec.destination_id == destination_id:
            return spec
    raise ValueError(f"unknown destination ID: {destination_id}")


def destinations_for_region(region_id, *, portal_only=True):
    region = get_region_spec(region_id)
    destinations = tuple(
        get_destination_spec(destination_id)
        for destination_id in region.destination_ids
    )
    if portal_only:
        destinations = tuple(
            destination for destination in destinations if destination.portal_visible
        )
    return destinations


def validate_region_manifest():
    destination_ids = tuple(spec.destination_id for spec in DESTINATION_SPECS)
    if len(destination_ids) != len(set(destination_ids)):
        raise ValueError("destination IDs must be unique")
    membership = tuple(
        destination_id
        for region in REGION_SPECS
        for destination_id in region.destination_ids
    )
    if len(membership) != len(set(membership)):
        raise ValueError("a destination may belong to only one region")
    if set(membership) != set(destination_ids):
        raise ValueError("every destination must have explicit region membership")
    region_membership = {
        destination_id: region.region_id
        for region in REGION_SPECS
        for destination_id in region.destination_ids
    }
    if any(
        region_membership[spec.destination_id] != spec.region_id
        for spec in DESTINATION_SPECS
    ):
        raise ValueError("destination region IDs must match authored membership")
    if any(
        spec.knowledge_fact_id is not None
        and spec.knowledge_fact_id not in M8_KNOWLEDGE_FACT_IDS
        for spec in DESTINATION_SPECS
    ):
        raise ValueError("destinations may reference only authored M8 facts")
    if len(M8_KNOWLEDGE_FACT_IDS) != len(set(M8_KNOWLEDGE_FACT_IDS)):
        raise ValueError("knowledge fact IDs must be unique")
    if tuple(fact_id for fact_id, _label in M8_KNOWLEDGE_FACT_LABELS) != (
        M8_KNOWLEDGE_FACT_IDS
    ):
        raise ValueError("every knowledge fact must have one authored label")
    return True


validate_region_manifest()


__all__ = [
    "DESTINATION_SPECS",
    "M8_ASHEN_ARENA_REVEALED_EVENT_ID",
    "M8_DROWNED_BRIEFING_EVENT_ID",
    "M8_KNOWLEDGE_FACT_IDS",
    "M8_KNOWLEDGE_FACT_LABELS",
    "REGION_SPECS",
    "DestinationSpec",
    "RegionSpec",
    "destinations_for_region",
    "get_destination_spec",
    "get_region_spec",
    "validate_region_manifest",
]

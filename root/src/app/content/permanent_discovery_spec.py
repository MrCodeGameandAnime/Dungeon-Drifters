"""Authored permanent-discovery source definitions."""

from dataclasses import dataclass
from enum import StrEnum


class PermanentDiscoveryType(StrEnum):
    ANCIENT_WELL = "ancient_well"
    FORGOTTEN_ALTAR = "forgotten_altar"
    SPIRIT_RELIC = "spirit_relic"


@dataclass(frozen=True)
class PermanentDiscoverySource:
    source_id: str
    discovery_type: PermanentDiscoveryType
    amount: int
    search_chance_bps: int | None = None

    def __post_init__(self):
        if not is_valid_permanent_discovery_source_id(self.source_id):
            raise ValueError("source_id must be a unique lowercase authored ID")
        try:
            discovery_type = PermanentDiscoveryType(self.discovery_type)
        except (TypeError, ValueError) as error:
            raise ValueError("unknown permanent discovery type") from error
        object.__setattr__(self, "discovery_type", discovery_type)
        if isinstance(self.amount, bool) or not isinstance(self.amount, int):
            raise TypeError("discovery amount must be an integer")
        allowed_amounts = {
            PermanentDiscoveryType.ANCIENT_WELL: {5, 10},
            PermanentDiscoveryType.FORGOTTEN_ALTAR: {5, 10},
            PermanentDiscoveryType.SPIRIT_RELIC: {3},
        }
        if self.amount not in allowed_amounts[discovery_type]:
            raise ValueError("discovery amount is not authored for its type")
        if self.search_chance_bps is not None:
            if isinstance(self.search_chance_bps, bool) or not isinstance(
                self.search_chance_bps, int
            ):
                raise TypeError("search_chance_bps must be an integer")
            if not 0 <= self.search_chance_bps <= 10000:
                raise ValueError("search_chance_bps must be between 0 and 10000")
def validate_permanent_discovery_sources(sources):
    try:
        values = tuple(sources)
    except TypeError as error:
        raise TypeError("sources must be an iterable of discovery sources") from error
    if any(not isinstance(source, PermanentDiscoverySource) for source in values):
        raise TypeError("sources must contain permanent discovery definitions")
    source_ids = tuple(source.source_id for source in values)
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("permanent discovery source IDs must be unique")
    return values


def is_valid_permanent_discovery_source_id(value):
    if not isinstance(value, str) or not 3 <= len(value) <= 80:
        return False
    if value[0] < "a" or value[0] > "z":
        return False
    return all(
        "a" <= character <= "z"
        or "0" <= character <= "9"
        or character == "_"
        for character in value
    )


__all__ = [
    "PermanentDiscoverySource",
    "PermanentDiscoveryType",
    "is_valid_permanent_discovery_source_id",
    "validate_permanent_discovery_sources",
]

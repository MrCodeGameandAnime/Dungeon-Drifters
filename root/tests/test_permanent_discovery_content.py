import importlib

import pytest

from app.content.permanent_discovery_spec import (
    PermanentDiscoverySource,
    PermanentDiscoveryType,
)


def test_floor_two_search_source_has_approved_authored_defaults():
    catalog = importlib.import_module("app.content.catalog")
    assert hasattr(catalog, "get_permanent_discovery_source")

    source = catalog.get_permanent_discovery_source("ancient_well_floor2_01")

    assert source.source_id == "ancient_well_floor2_01"
    assert source.discovery_type.value == "ancient_well"
    assert source.amount == 5
    assert source.search_chance_bps == 1000


def test_unknown_permanent_discovery_source_is_not_cataloged():
    catalog = importlib.import_module("app.content.catalog")
    assert hasattr(catalog, "get_permanent_discovery_source")

    try:
        catalog.get_permanent_discovery_source("ancient_well_unknown")
    except ValueError as error:
        assert "unknown permanent discovery source" in str(error)
    else:
        raise AssertionError("unknown discovery source was returned by the catalog")


@pytest.mark.parametrize(
    ("chance", "error"),
    (
        (True, TypeError),
        (-1, ValueError),
        (10001, ValueError),
    ),
)
def test_discovery_source_rejects_invalid_search_chance(chance, error):
    with pytest.raises(error, match="search_chance_bps"):
        PermanentDiscoverySource(
            "ancient_well_test_01",
            PermanentDiscoveryType.ANCIENT_WELL,
            5,
            search_chance_bps=chance,
        )

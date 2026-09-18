from pathlib import Path
from types import MappingProxyType

import pytest

import app.readonly_mapping as readonly_mapping_module
from app.content.catalog import get_enemy_spec
from app.content.weapon_spec import WeaponSpec
from app.readonly_mapping import readonly_mapping


ROOT = Path(__file__).resolve().parents[1]


def test_cpython_uses_native_mapping_proxy():
    assert isinstance(readonly_mapping({"value": 1}), MappingProxyType)


def test_fallback_exposes_only_the_required_read_surface(monkeypatch):
    monkeypatch.setattr(readonly_mapping_module, "_NATIVE_MAPPING_PROXY", None)
    source = {"first": 1, "second": 2}

    mapping = readonly_mapping(source)

    assert mapping["first"] == 1
    assert "second" in mapping
    assert tuple(mapping) == ("first", "second")
    assert len(mapping) == 2
    assert tuple(mapping.keys()) == ("first", "second")
    assert tuple(mapping.items()) == (("first", 1), ("second", 2))
    assert dict(mapping) == source

    with pytest.raises(TypeError):
        mapping["first"] = 99
    with pytest.raises(TypeError):
        del mapping["first"]
    with pytest.raises(AttributeError):
        mapping.clear()

    source["first"] = 99
    assert mapping["first"] == 1


def test_catalog_mapping_remains_read_only():
    import app.content.catalog as catalog_module

    assert catalog_module._ENEMY_CATALOG["goblin"] is get_enemy_spec("goblin")
    with pytest.raises(TypeError):
        catalog_module._ENEMY_CATALOG["replacement"] = get_enemy_spec("goblin")


def test_weapon_spec_stat_bonuses_remain_read_only():
    spec = WeaponSpec(
        item_id="test_weapon",
        persistence_key="TestWeapon",
        name="Test Weapon",
        weapon_type="Test Type",
        intended_wielder="Tester",
        stat_bonuses={"strength": 1},
        value=0,
        description="Test description.",
    )

    assert spec.stat_bonuses["strength"] == 1
    with pytest.raises(TypeError):
        spec.stat_bonuses["strength"] = 99


def test_production_has_no_direct_mapping_proxy_imports_outside_helper():
    helper = ROOT / "src" / "app" / "readonly_mapping.py"

    for path in (ROOT / "src" / "app").rglob("*.py"):
        if path == helper:
            continue
        assert "MappingProxyType" not in path.read_text(encoding="utf-8"), path

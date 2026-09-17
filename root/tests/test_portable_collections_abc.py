import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
OVERLAY_ROOT = ROOT / "portability" / "micropython"


def _run_forced_compatibility(source):
    prelude = (
        "import sys\n"
        "import enum\n"
        "import keyword\n"
        "import re\n"
        "import dataclasses\n"
        "import collections as native_collections\n"
        "import collections.abc as native_abc\n"
        f"sys.path.insert(0, {str(OVERLAY_ROOT)!r})\n"
        f"sys.path.insert(1, {str(SRC_ROOT)!r})\n"
        "from collections_abc_compat import install\n"
        "proxy = install(native_collections, object)\n"
        "assert install(native_collections, object) is proxy\n"
        "sys.modules['collections.abc'] = proxy\n"
    )
    return subprocess.run(
        [sys.executable, "-S", "-c", prelude + source],
        cwd=ROOT,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
    )


def test_native_cpython_uses_standard_library_collections_abc():
    import collections.abc as native_abc

    assert Path(native_abc.__file__).resolve().parent != OVERLAY_ROOT.resolve()


def test_forced_compatibility_injects_only_the_qualified_child_module():
    result = _run_forced_compatibility(
        """
import collections
import collections.abc as native_child
from collections.abc import Mapping, Sequence

assert getattr(sys.modules["collections.abc"], "_dd_myp8_module", False) is True
assert proxy._native_collections is native_collections
assert proxy.Mapping is native_abc.Mapping
assert proxy.Sequence is native_abc.Sequence
assert native_collections.Counter is collections.Counter
assert getattr(proxy, "Counter", None) is None
assert native_child is not proxy
assert Mapping is native_abc.Mapping
assert Sequence is native_abc.Sequence
"""
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_forced_compatibility_preserves_mapping_and_sequence_contracts():
    result = _run_forced_compatibility(
        """
from collections.abc import Mapping, Sequence
from app.readonly_mapping import _ReadonlyMapping, readonly_mapping

wrapped = readonly_mapping({"strength": 2})
assert isinstance({}, Mapping)
assert isinstance(wrapped, Mapping)
assert not isinstance(object(), Mapping)
assert isinstance([], Sequence)
assert isinstance((), Sequence)
assert not isinstance(set(), Sequence)
assert not isinstance((value for value in (1, 2)), Sequence)
assert Mapping[str, int]

from app.combat.battle import Battle
from app.content.catalog import create_enemy_definition
from app.enemies.state import EnemyState

enemy = EnemyState(create_enemy_definition("goblin"))
assert Battle._normalize_enemies([enemy]) == (enemy,)
assert Battle._normalize_enemies((enemy,)) == (enemy,)
for invalid in ("text", b"text", bytearray(b"text"), set(), (value for value in (1, 2))):
    try:
        Battle._normalize_enemies(invalid)
    except TypeError:
        pass
    else:
        raise AssertionError("invalid enemy collection was accepted")
"""
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_forced_compatibility_exercises_real_weapon_paths():
    result = _run_forced_compatibility(
        """
from app.content.catalog import get_weapon_spec
from app.content.weapon_spec import WeaponSpec
from app.items.weapon import Weapon

weapon = Weapon(
    item_id="probe_weapon",
    persistence_key="probe_key",
    name="Probe Weapon",
    weapon_type="sword",
    intended_wielder="branoc",
    stat_bonuses={"strength": 2},
    value=1,
    description="probe",
)
assert weapon.stat_bonuses == {"strength": 2}

spec = WeaponSpec(
    item_id="probe_weapon",
    persistence_key="probe_key",
    name="Probe Weapon",
    weapon_type="sword",
    intended_wielder="branoc",
    stat_bonuses={"strength": 2},
    value=1,
    description="probe",
)
assert spec.stat_bonuses == {"strength": 2}
created = spec.create_weapon()
assert created.stat_bonuses == {"strength": 2}
assert get_weapon_spec("sunder_spire").create_weapon().item_id == "sunder_spire"
"""
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_forced_compatibility_preserves_existing_identifier_validation():
    result = _run_forced_compatibility(
        """
from app.content.catalog import get_drifter_spec, get_enemy_spec, get_weapon_spec
from app.content.drifter_spec import DrifterSpec
from app.content.enemy_spec import EnemySpec
from app.content.route_spec import validate_content_id
from app.content.weapon_spec import WeaponSpec

def replace_value(instance, field_name, value):
    values = {name: getattr(instance, name) for name in instance.__dataclass_fields__}
    values[field_name] = value
    return values

for factory, field_name in (
    (get_enemy_spec("goblin"), "archetype_id"),
    (get_drifter_spec("branoc"), "drifter_id"),
    (get_weapon_spec("sunder_spire"), "item_id"),
):
    for value in ("goblin_2", "ember_shard"):
        candidate_type = type(factory)
        try:
            candidate_type(**replace_value(factory, field_name, value))
        except ValueError:
            pass

assert validate_content_id("route_id", "dungeon_entrance") == "dungeon_entrance"
for value in ("class", "for", "return", "has-dash", "two words", "_leading", ""):
    for constructor in (
        lambda value=value: EnemySpec(**replace_value(get_enemy_spec("goblin"), "archetype_id", value)),
        lambda value=value: DrifterSpec(**replace_value(get_drifter_spec("branoc"), "drifter_id", value)),
        lambda value=value: WeaponSpec(**replace_value(get_weapon_spec("sunder_spire"), "item_id", value)),
        lambda value=value: validate_content_id("route_id", value),
    ):
        try:
            constructor()
        except (TypeError, ValueError):
            pass
        else:
            raise AssertionError("invalid content ID was accepted")
"""
    )
    assert result.returncode == 0, result.stdout + result.stderr

"""Host composition for a default local-first save port."""

import os
from pathlib import Path
from uuid import uuid4

from app.persistence.coordinator import SaveCoordinator
from app.persistence.local_store import LocalProfileStore
from app.persistence.migration import migrate_legacy_save


def default_profile_root(*, system=None, environ=None, home=None):
    environment = os.environ if environ is None else environ
    if system is None:
        system = os.name
    platform = str(system).lower()
    home_path = Path.home() if home is None else Path(home)

    if platform in {"nt", "windows"}:
        base = environment.get("LOCALAPPDATA") or environment.get("APPDATA")
        if base is None:
            base = home_path / "AppData" / "Local"
        return Path(base) / "Dungeon Drifters"

    base = environment.get("XDG_DATA_HOME")
    if base is None:
        base = home_path / ".local" / "share"
    return Path(base) / "dungeon-drifters"


def legacy_save_path():
    return Path(__file__).resolve().parents[2] / "saves" / "dungeon_drifters.json"


def build_default_save_port(
    *,
    storage_root=None,
    legacy_path=None,
    profile_id_factory=uuid4,
    client_save_id_factory=uuid4,
    now_factory=None,
):
    if storage_root is None:
        storage_root = default_profile_root()
    if legacy_path is None:
        legacy_path = legacy_save_path()
    store = LocalProfileStore(storage_root)
    migration_options = {
        "profile_id_factory": profile_id_factory,
        "client_save_id_factory": client_save_id_factory,
    }
    coordinator_options = {
        "client_save_id_factory": client_save_id_factory,
    }
    if now_factory is not None:
        migration_options["now_factory"] = now_factory
        coordinator_options["now_factory"] = now_factory

    migration_result = migrate_legacy_save(
        legacy_path,
        store,
        **migration_options,
    )
    profile_ids = store.list_profiles()
    profile_id = profile_ids[0] if profile_ids else profile_id_factory()
    return SaveCoordinator(
        store,
        profile_id,
        migration_result=migration_result,
        **coordinator_options,
    )


__all__ = [
    "build_default_save_port",
    "default_profile_root",
    "legacy_save_path",
]

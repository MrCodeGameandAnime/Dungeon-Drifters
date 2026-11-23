"""Thin browser translation boundary around the authoritative DD runtime."""

import json
from dataclasses import fields, is_dataclass
from enum import Enum
from uuid import UUID

from app.combat.battle import Battle
from app.content.catalog import DRIFTER_SPECS, create_enemy_state
from app.game.browser_test_scenarios import build_browser_test_scenario
from app.game.new_game import create_new_game
from app.game.overworld_session import OverworldSession
from app.player.run_items import InventoryCommand
from app.persistence.coordinator import SaveCoordinator
from app.persistence.envelope import (
    ProfileEnvelope,
    SyncState,
    parse_profile_envelope,
    serialize_profile_envelope,
)
from app.persistence.ports import (
    ProfileStoreError,
    ProfileStoreResult,
    ProfileStoreStatus,
)
from app.persistence.save_port_contract import SaveLoadStatus
from app.ui.battle_ui import (
    ChooseAction,
    ChooseHealingTarget,
    ChooseInventoryCommand,
    ChooseInventoryCompanion,
    ChooseInventoryItem,
    ChooseMove,
    ChooseTarget,
    ConfirmInventoryUse,
    GoBack,
)
from app.ui.overworld_ui import (
    ChooseActivePair,
    ChooseDestination,
    ChooseBlacksmithInstallComponent,
    ChooseDiscoverySearcher,
    ChooseDiscoveryTarget,
    ChooseExpeditionPlan,
    ChooseExpeditionReport,
    ChooseAdvancementEquip,
    ChooseAdvancementPurchase,
    ChooseCompanion,
    ChooseFloorTwoBossHelper,
    ChooseRegion,
    ChooseCharacterTarget,
    ChooseMerchantCraftComponent,
    ChooseMerchantDismantle,
    ChooseMerchantImprove,
    ChooseMerchantTarget,
    ChooseMerchantTierV,
    ChooseHubBuyback,
    ChooseHubSupplyAction,
    ChooseAlchemyRecipe,
    ChooseEquipmentAction,
    ChooseEquipmentConfirmation,
    ChooseEquipmentInstance,
    EquipmentOperation,
    ChooseOverworldAction,
    ChooseOverworldHealingTarget,
    ChooseOverworldItem,
    ChoosePermanentStatIncrease,
    ChooseWeaponTarget,
)


_DRIFTER_SPRITE_URLS = {
    "branoc": "assets/drifters/branoc.png",
    "azhvielle": "assets/drifters/azhvielle.png",
    "zhaivra": "assets/drifters/zhaivra.png",
    "joruun": "assets/drifters/joruun.png",
}
_BROWSER_PROFILE_ID = UUID("d4d4d4d4-0000-4000-8000-000000000001")
_BROWSER_PROFILE_KEY = "dungeon-drifters.profile.v1." + str(_BROWSER_PROFILE_ID)


def _is_missing_storage_value(value):
    if value is None:
        return True
    try:
        from pyodide.ffi import jsnull
    except ImportError:
        return False
    return value is jsnull


class BrowserLocalProfileStore:
    """Store the canonical local profile envelope in browser localStorage."""

    def __init__(self, storage):
        self._storage = storage
        self._write_authorized = False

    def authorize_existing_profile(self):
        """Allow writes after an explicit Continue or replacement decision."""
        if self.load(_BROWSER_PROFILE_ID).status is not ProfileStoreStatus.VALID:
            return False
        self._write_authorized = True
        return True

    def revoke_write_authorization(self):
        self._write_authorized = False

    def inspect(self, profile_id):
        result = self.load(profile_id)
        if result.status is ProfileStoreStatus.VALID:
            return ProfileStoreResult(status=ProfileStoreStatus.VALID)
        return result

    def load(self, profile_id):
        if profile_id != _BROWSER_PROFILE_ID:
            return ProfileStoreResult(status=ProfileStoreStatus.MISSING)
        try:
            encoded = self._storage.getItem(_BROWSER_PROFILE_KEY)
        except Exception:
            return ProfileStoreResult(
                status=ProfileStoreStatus.INVALID,
                error="The browser save could not be read.",
            )
        if _is_missing_storage_value(encoded):
            return ProfileStoreResult(status=ProfileStoreStatus.MISSING)
        try:
            envelope = parse_profile_envelope(str(encoded).encode("utf-8"))
        except (TypeError, ValueError):
            return ProfileStoreResult(
                status=ProfileStoreStatus.INVALID,
                error="The browser save is invalid and was not loaded.",
            )
        if (
            envelope.profile_id != _BROWSER_PROFILE_ID
            or envelope.account_id is not None
            or envelope.remote_revision is not None
            or envelope.sync_state is not SyncState.LOCAL_ONLY
        ):
            return ProfileStoreResult(
                status=ProfileStoreStatus.INVALID,
                error="The browser save has an unsupported profile state.",
            )
        return ProfileStoreResult(
            status=ProfileStoreStatus.VALID,
            envelope=envelope,
        )

    def save(self, envelope):
        if not isinstance(envelope, ProfileEnvelope):
            raise TypeError("envelope must be a ProfileEnvelope")
        if (
            envelope.profile_id != _BROWSER_PROFILE_ID
            or envelope.account_id is not None
            or envelope.remote_revision is not None
            or envelope.sync_state is not SyncState.LOCAL_ONLY
        ):
            raise ProfileStoreError("browser storage accepts local-only profiles")
        encoded = serialize_profile_envelope(envelope).decode("utf-8")
        current = self.load(_BROWSER_PROFILE_ID)
        if current.status is ProfileStoreStatus.INVALID:
            raise ProfileStoreError("existing browser profile is invalid")
        if current.status is ProfileStoreStatus.VALID:
            if not self._write_authorized:
                raise ProfileStoreError(
                    "existing browser profile requires an explicit startup decision"
                )
            previous = current.envelope
            if envelope.local_sequence < previous.local_sequence:
                raise ProfileStoreError("local profile sequence cannot go backwards")
            if envelope.local_sequence == previous.local_sequence and (
                envelope.client_save_id != previous.client_save_id
                or envelope.payload_sha256 != previous.payload_sha256
            ):
                raise ProfileStoreError(
                    "a changed local payload requires a new sequence and save ID"
                )
            if (
                envelope.local_sequence > previous.local_sequence
                and envelope.client_save_id == previous.client_save_id
            ):
                raise ProfileStoreError("a new local sequence requires a new save ID")
        try:
            self._storage.setItem(_BROWSER_PROFILE_KEY, encoded)
        except Exception as error:
            raise ProfileStoreError("browser profile could not be saved") from error
        committed = self.load(_BROWSER_PROFILE_ID)
        if (
            committed.status is not ProfileStoreStatus.VALID
            or committed.envelope != envelope
        ):
            raise ProfileStoreError("saved browser profile did not validate after commit")
        self._write_authorized = True

    def list_profiles(self):
        result = self.load(_BROWSER_PROFILE_ID)
        if result.status is ProfileStoreStatus.VALID:
            return (_BROWSER_PROFILE_ID,)
        return ()


def _get_browser_storage():
    try:
        from js import localStorage
    except ImportError:
        return None
    return localStorage


def _project(value):
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {field.name: _project(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_project(item) for item in value]
    if isinstance(value, list):
        return [_project(item) for item in value]
    if isinstance(value, dict):
        return {_project(key): _project(item) for key, item in value.items()}
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    raise TypeError("unsupported browser projection value")


def _required(command, key):
    if key not in command:
        raise ValueError("browser command requires " + key)
    return command[key]


def _command_to_input(command):
    if not isinstance(command, dict):
        raise TypeError("browser command must be an object")
    kind = command.get("kind")
    if kind == "overworld_action":
        return ChooseOverworldAction(_required(command, "action"))
    if kind == "overworld_item":
        return ChooseOverworldItem(_required(command, "selection_key"))
    if kind == "overworld_healing_target":
        return ChooseOverworldHealingTarget(_required(command, "drifter_id"))
    if kind == "companion":
        return ChooseCompanion(
            _required(command, "drifter_id"),
            _required(command, "event_id"),
        )
    if kind == "floor_two_boss_helper":
        return ChooseFloorTwoBossHelper(_required(command, "drifter_id"))
    if kind == "active_pair":
        return ChooseActivePair(tuple(_required(command, "drifter_ids")))
    if kind == "region":
        return ChooseRegion(_required(command, "region_id"))
    if kind == "destination":
        return ChooseDestination(_required(command, "destination_id"))
    if kind == "discovery_searcher":
        return ChooseDiscoverySearcher(_required(command, "drifter_id"))
    if kind == "discovery_target":
        return ChooseDiscoveryTarget(_required(command, "drifter_id"))
    if kind == "expedition_plan":
        return ChooseExpeditionPlan(
            _required(command, "destination_floor_id"),
            _required(command, "category"),
        )
    if kind == "expedition_report":
        return ChooseExpeditionReport(_required(command, "report_id"))
    if kind == "character_target":
        return ChooseCharacterTarget(_required(command, "drifter_id"))
    if kind == "stat_increase":
        return ChoosePermanentStatIncrease(_required(command, "stat_name"))
    if kind == "advancement_purchase":
        return ChooseAdvancementPurchase(
            _required(command, "drifter_id"),
            _required(command, "skill_id"),
        )
    if kind == "advancement_equip":
        return ChooseAdvancementEquip(
            _required(command, "drifter_id"),
            _required(command, "move_id"),
            _required(command, "slot"),
        )
    if kind == "merchant_target":
        return ChooseMerchantTarget(_required(command, "drifter_id"))
    if kind == "merchant_improve":
        return ChooseMerchantImprove(
            _required(command, "target_drifter_id"),
            _required(command, "slot_id"),
            command.get("expected_transaction_sequence", 0),
        )
    if kind == "merchant_dismantle":
        return ChooseMerchantDismantle(
            _required(command, "target_drifter_id"),
            _required(command, "item_id"),
            command.get("quantity", 1),
            command.get("expected_transaction_sequence", 0),
        )
    if kind == "merchant_craft_component":
        return ChooseMerchantCraftComponent(
            _required(command, "target_drifter_id"),
            _required(command, "component_id"),
            command.get("expected_transaction_sequence", 0),
        )
    if kind == "merchant_tier_v":
        return ChooseMerchantTierV(
            _required(command, "target_drifter_id"),
            command.get("expected_transaction_sequence", 0),
        )
    if kind == "blacksmith_install_component":
        return ChooseBlacksmithInstallComponent(
            _required(command, "target_drifter_id"),
            _required(command, "component_id"),
            command.get("expected_transaction_sequence", 0),
        )
    if kind == "hub_buyback":
        return ChooseHubBuyback(
            _required(command, "sale_id"),
            command.get("quantity", 1),
            command.get("expected_transaction_sequence", 0),
        )
    if kind == "hub_supply":
        return ChooseHubSupplyAction(
            _required(command, "operation"),
            _required(command, "item_id"),
            command.get("expected_transaction_sequence", 0),
            command.get("quantity", 1),
        )
    if kind == "alchemy_recipe":
        return ChooseAlchemyRecipe(
            _required(command, "recipe_id"),
            command.get("expected_transaction_sequence", 0),
        )
    if kind == "weapon_target":
        return ChooseWeaponTarget(_required(command, "drifter_id"))
    if kind == "equipment_instance":
        return ChooseEquipmentInstance(_required(command, "instance_id"))
    if kind == "equipment_action":
        return ChooseEquipmentAction(
            _required(command, "target_drifter_id"),
            _required(command, "equipment_instance_id"),
            EquipmentOperation(_required(command, "operation")),
            command.get("modifier_instance_id"),
            command.get("affix_id"),
            command.get("expected_transaction_sequence", 0),
        )
    if kind == "equipment_confirmation":
        return ChooseEquipmentConfirmation(_required(command, "confirmed"))
    if kind == "action":
        return ChooseAction(_required(command, "intent"))
    if kind == "move":
        return ChooseMove(_required(command, "key"))
    if kind == "target":
        return ChooseTarget(_required(command, "target_id"))
    if kind == "healing_target":
        return ChooseHealingTarget(
            _required(command, "target_id"),
            command.get("item_id", "healing_potion"),
        )
    if kind == "inventory_item":
        return ChooseInventoryItem(_required(command, "item_id"))
    if kind == "inventory_command":
        return ChooseInventoryCommand(_required(command, "command"))
    if kind == "inventory_companion":
        return ChooseInventoryCompanion(_required(command, "item_id"))
    if kind == "inventory_confirm":
        return ConfirmInventoryUse(_required(command, "confirmed"))
    if kind == "back":
        return GoBack()
    raise ValueError("unknown browser command: " + str(kind))


def drifter_roster():
    return [
        {
            "drifter_id": profile.drifter_id,
            "choice": profile.choice,
            "short_name": profile.short_name,
            "archetype_name": profile.archetype_name,
            "combat_role": profile.combat_role,
            "selection_summary": profile.selection_summary,
            "sprite_url": _DRIFTER_SPRITE_URLS[profile.drifter_id],
        }
        for profile in DRIFTER_SPECS
    ]


def _activate_session(runtime, game, drifter_id, adventure_text=None):
    runtime._game = game
    runtime._session = OverworldSession(
        game,
        ui=None,
        battle_factory=Battle,
        enemy_factory=create_enemy_state,
        battle_ui_factory=None,
        save_port=runtime._save_port,
    )
    runtime._session._adventure_text = adventure_text
    runtime._drifter_id = drifter_id


class BrowserRuntime:
    def __init__(self, storage=None):
        self._game = None
        self._session = None
        self._drifter_id = None
        self._storage = _get_browser_storage() if storage is None else storage
        self._profile_store = (
            None
            if self._storage is None
            else BrowserLocalProfileStore(self._storage)
        )
        self._save_port = (
            None
            if self._profile_store is None
            else SaveCoordinator(self._profile_store, _BROWSER_PROFILE_ID)
        )
        self._new_game_confirmed = False
        self._new_game_session_authorized = False

    def startup_status(self):
        if self._save_port is None:
            return {"status": "missing"}
        result = self._save_port.inspect()
        if result.status is SaveLoadStatus.VALID:
            return {"status": "valid"}
        if result.status is SaveLoadStatus.INVALID:
            return {
                "status": "invalid",
                "error": result.error or "The browser save could not be read.",
            }
        return {"status": "missing"}

    def request_new_game(self):
        status = self.startup_status()
        if status["status"] == "valid":
            return {"status": "confirmation"}
        if status["status"] == "invalid":
            return {"status": "blocked", "error": status["error"]}
        return {"status": "selection"}

    def confirm_new_game(self, confirmed):
        if not isinstance(confirmed, bool):
            raise TypeError("confirmed must be a bool")
        if not confirmed:
            return self.startup_status()
        status = self.startup_status()
        if status["status"] == "invalid":
            return {"status": "blocked", "error": status["error"]}
        if status["status"] == "valid":
            if not self._profile_store.authorize_existing_profile():
                return {
                    "status": "blocked",
                    "error": "The browser save changed and could not be confirmed.",
                }
        self._new_game_confirmed = True
        return {"status": "selection"}

    def continue_game(self):
        status = self.startup_status()
        if status["status"] != "valid":
            return {
                "status": status["status"],
                "error": status.get("error"),
            }
        if not self._profile_store.authorize_existing_profile():
            return {
                "status": "invalid",
                "error": "The browser save changed and could not be loaded.",
            }
        result = self._save_port.load()
        if result.status is not SaveLoadStatus.LOADED:
            self._profile_store.revoke_write_authorization()
            return {"status": "invalid", "error": result.error}
        game = result.game_state
        drifter_id = game.player_state.character.profile.drifter_id
        self._new_game_confirmed = False
        self._new_game_session_authorized = False
        _activate_session(self, game, drifter_id)
        return {"status": "loaded", "view": self.current_view()}

    def _authorize_new_game_start(self, *, allow_current_new_game=False):
        status = self.startup_status()
        if status["status"] == "invalid":
            raise ProfileStoreError(status["error"])
        if status["status"] == "valid":
            if self._new_game_confirmed:
                if not self._profile_store.authorize_existing_profile():
                    raise ProfileStoreError(
                        "the browser save changed before replacement was confirmed"
                    )
            elif not (
                allow_current_new_game and self._new_game_session_authorized
            ):
                raise ProfileStoreError(
                    "continue the saved game or confirm starting a new game"
                )
        self._new_game_confirmed = False
        self._new_game_session_authorized = True

    def start_game(self, drifter_id="branoc"):
        game = create_new_game(drifter_id)
        self._authorize_new_game_start()
        _activate_session(self, game, drifter_id)
        return self.current_view()

    def load_scenario(self, code):
        game, drifter_id, adventure_text = build_browser_test_scenario(code)
        self._authorize_new_game_start(allow_current_new_game=True)
        _activate_session(self, game, drifter_id, adventure_text)
        return self.current_view()

    def current_view(self):
        if self._session is None:
            raise RuntimeError("browser runtime has not started")
        return _project(self._session.current_view())

    def current_view_json(self):
        return json.dumps(self.current_view(), separators=(",", ":"))

    def current_expedition_clock_text(self):
        if self._session is None:
            raise RuntimeError("browser runtime has not started")
        return self._session.current_expedition_clock_text()

    def submit(self, command):
        if self._session is None:
            raise RuntimeError("browser runtime has not started")
        return _project(self._session.submit(_command_to_input(command)))

    def submit_json(self, command_json):
        return self.submit(json.loads(command_json))

    def restart_game(self):
        return self.start_game(self._drifter_id or "branoc")


_runtime = BrowserRuntime()


def start_game(drifter_id="branoc"):
    return _runtime.start_game(drifter_id)


def current_view():
    return _runtime.current_view()


def current_expedition_clock_text():
    return _runtime.current_expedition_clock_text()


def submit(command):
    return _runtime.submit(command)


def restart_game():
    return _runtime.restart_game()


def startup_status():
    return _runtime.startup_status()


def request_new_game():
    return _runtime.request_new_game()


def confirm_new_game(confirmed):
    return _runtime.confirm_new_game(confirmed)


def continue_game():
    return _runtime.continue_game()


def load_scenario(code):
    return _runtime.load_scenario(code)

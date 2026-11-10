"""Schema-23 save documents and canonical in-memory reconstruction."""

from copy import deepcopy
from uuid import UUID

from app.content.catalog import (
    create_weapon_from_persistence_key,
    get_drifter_spec_by_choice,
    get_known_permanent_discovery_source,
    get_route_node_spec,
    get_route_spec,
    get_weapon_spec,
)
from app.content.hub_economy import get_supply_item
from app.content.equipment_spec import get_equipment_template
from app.content.permanent_discovery_spec import (
    is_valid_permanent_discovery_source_id,
)
from app.content.route_spec import RouteNodeKind
from app.content.weapon_progression_spec import (
    MAX_CRAFTING_EXPERIENCE,
    get_weapon_component_spec,
)
from app.game.game_state import GameState
from app.game.overworld_state import ContextualRoutePhase, OverworldState
from app.game.party_state import (
    DungeonPhase,
    PartyState,
    validate_run_event_history,
)
from app.game.story_state import StoryState
from app.game.world_state import WorldState
from app.items.equipment import EquipmentInstance
from app.items.armor_modifier import ArmorModifierInstance
from app.player.character_run_state import (
    CharacterRunCheckpoint,
    InfusionKind,
    PreparedPayloadId,
    RunItemId,
)
from app.player.advancement_state import AdvancementState, move_ids_for_kit
from app.player.player_state import PlayerState
from app.player.progression import (
    MAXIMUM_LEVEL,
    MINIMUM_LEVEL,
    xp_required_for_next_level,
)
from app.player.resources import Super
from app.player.stats import PermanentStats
from app.snapshot import STATE_SCHEMA_VERSION, validate_plain_value


_SURFACE_ROUTE = get_route_spec("surface")
_FLOOR_ONE_ROUTE = get_route_spec("floor_one")
_FLOOR_TWO_ROUTE = get_route_spec("floor_two")
_FLOOR_THREE_ROUTE = get_route_spec("floor_three")
_SURFACE_ROUTE_NODE_IDS = tuple(node.node_id for node in _SURFACE_ROUTE.nodes)
_SURFACE_REST_NODE_IDS = tuple(
    node.node_id
    for node in _SURFACE_ROUTE.nodes
    if node.kind is RouteNodeKind.REST
)
_SURFACE_ENCOUNTER_NODES = {
    node.encounter_id: node
    for node in _SURFACE_ROUTE.nodes
    if node.encounter_id is not None
}
_FIRST_SURFACE_NODE_ID = _SURFACE_ROUTE_NODE_IDS[0]
_DUNGEON_ENTRANCE_NODE_ID = _SURFACE_ROUTE_NODE_IDS[-1]
_FLOOR_ONE_ROUTE_NODE_IDS = tuple(
    node.node_id for node in _FLOOR_ONE_ROUTE.nodes
)
_FLOOR_ONE_REST_NODE_IDS = tuple(
    node.node_id
    for node in _FLOOR_ONE_ROUTE.nodes
    if node.kind is RouteNodeKind.REST
)
_FLOOR_TWO_ROUTE_NODE_IDS = tuple(
    node.node_id for node in _FLOOR_TWO_ROUTE.nodes
)
_FLOOR_TWO_REST_NODE_IDS = tuple(
    node.node_id
    for node in _FLOOR_TWO_ROUTE.nodes
    if node.kind is RouteNodeKind.REST
)
_FLOOR_THREE_ROUTE_NODE_IDS = tuple(
    node.node_id for node in _FLOOR_THREE_ROUTE.nodes
)


_LEGACY_RUNTIME_SCHEMA_VERSION = 7
_LEGACY_DISK_SCHEMA_VERSION = 8
_PREVIOUS_DISK_SCHEMA_VERSION = 9
_PREVIOUS_CURRENT_DISK_SCHEMA_VERSION = 10
_CURRENT_PREVIOUS_DISK_SCHEMA_VERSION = 11
_PREVIOUS_DISK_SCHEMA_VERSION_CURRENT = 12
_LATEST_PREVIOUS_DISK_SCHEMA_VERSION = 13
_PREVIOUS_CURRENT_DISK_SCHEMA_VERSION_CURRENT = 14
_LATEST_PREVIOUS_CURRENT_DISK_SCHEMA_VERSION_CURRENT = 15
_PRE_RESPEC_DISK_SCHEMA_VERSION = 16
_PRE_RUN_EVENT_DISK_SCHEMA_VERSION = 17
_PRE_EQUIPMENT_DISK_SCHEMA_VERSION = 18
_PRE_GENERATED_EQUIPMENT_DISK_SCHEMA_VERSION = 19
_PRE_ALCHEMIST_DISK_SCHEMA_VERSION = 20
_PRE_BOSS_HELPER_DISK_SCHEMA_VERSION = 21
_PRE_FLOOR_THREE_DISK_SCHEMA_VERSION = 22
DISK_SCHEMA_VERSION = 23


class SaveStateValidationError(ValueError):
    """Raised when a disk save cannot be trusted or reconstructed."""


def build_save_document(game_state):
    if not isinstance(game_state, GameState):
        raise TypeError("game_state must be a GameState instance")

    source = deepcopy(game_state.snapshot())
    _require_int(source.get("schema_version"), "game.schema_version")
    player = source.get("player")
    if not isinstance(player, dict):
        raise SaveStateValidationError("game.player must be an object")
    identity = player.get("identity")
    if not isinstance(identity, dict):
        raise SaveStateValidationError("player.identity must be an object")
    profile = identity.get("profile")
    if profile is None:
        raise SaveStateValidationError(
            "disk saves require a selected canonical character profile"
        )
    player.pop("combat", None)
    _strip_companion_combat(source.get("party"))
    source["schema_version"] = DISK_SCHEMA_VERSION
    _validate_document(
        source,
        schema_version=DISK_SCHEMA_VERSION,
        require_active_run_scope=True,
    )
    return source


def migrate_schema_7(document):
    _validate_plain_document(document)
    schema_version = document.get("schema_version")
    if schema_version != _LEGACY_RUNTIME_SCHEMA_VERSION:
        raise SaveStateValidationError(
            "only schema 7 documents can be migrated"
        )

    migrated = deepcopy(document)
    migrated["schema_version"] = DISK_SCHEMA_VERSION
    overworld = migrated.get("overworld")
    missing_overworld = not isinstance(overworld, dict) or not {
        "current_route_node_id",
        "surface_route_begun",
        "dungeon_entrance_reached",
        "route_complete",
        "resolved_rest_node_ids",
        "current_contextual_route_phase",
    }.issubset(overworld)
    if missing_overworld:
        migrated["overworld"] = _opening_overworld_snapshot()
    elif isinstance(migrated["overworld"], dict):
        migrated["overworld"].setdefault("active_route_id", "surface")
    migrated.setdefault("metadata", {})
    migrated.setdefault("story", _empty_story_snapshot())
    migrated.setdefault("world", _empty_world_snapshot())
    player = migrated.get("player")
    if isinstance(player, dict):
        player.pop("combat", None)
    if missing_overworld and isinstance(migrated.get("world"), dict):
        defeated = migrated["world"].get("defeated_encounters", [])
        migrated["world"]["defeated_encounters"] = [
            encounter_id
            for encounter_id in defeated
            if encounter_id not in _SURFACE_ENCOUNTER_NODES
        ]
    _add_legacy_party_state(migrated)
    _add_signature_weapon_defaults(migrated)
    _add_legacy_active_drifter_ids(migrated)
    _add_advancement_defaults(migrated)
    _add_permanent_discovery_defaults(migrated)
    _add_floor_two_defaults(migrated)
    _add_equipment_defaults(migrated)
    _validate_document(migrated, schema_version=DISK_SCHEMA_VERSION)
    return migrated


def migrate_schema_8(document):
    """Upgrade an original disk schema-8 payload without changing its input."""
    _validate_plain_document(document)
    _validate_legacy_schema8_document(document)
    migrated = deepcopy(document)
    migrated["schema_version"] = DISK_SCHEMA_VERSION
    _add_legacy_party_state(migrated)
    migrated["overworld"].setdefault("active_route_id", "surface")
    _add_signature_weapon_defaults(migrated)
    _add_legacy_active_drifter_ids(migrated)
    _add_advancement_defaults(migrated)
    _add_permanent_discovery_defaults(migrated)
    _add_floor_two_defaults(migrated)
    _add_equipment_defaults(migrated)
    _validate_document(migrated, schema_version=DISK_SCHEMA_VERSION)
    return migrated


def migrate_schema_9(document):
    """Upgrade an original disk schema-9 payload without changing its input."""
    _validate_legacy_current_document(document)
    return _migrate_previous_current_document(document)


def migrate_schema_10(document):
    """Upgrade a schema-10 save without changing its input."""
    validate_legacy_schema10_document(document)
    return _migrate_previous_current_document(document)


def migrate_schema_11(document):
    """Upgrade a schema-11 save without changing its input."""
    validate_legacy_schema11_document(document)
    migrated = deepcopy(document)
    migrated["schema_version"] = DISK_SCHEMA_VERSION
    _add_tier_v_success_defaults(migrated)
    _add_legacy_active_drifter_ids(migrated)
    _add_carried_supply_defaults(migrated)
    _add_advancement_defaults(migrated)
    _add_permanent_discovery_defaults(migrated)
    _add_floor_two_defaults(migrated)
    _add_equipment_defaults(migrated)
    _validate_document(migrated, schema_version=DISK_SCHEMA_VERSION)
    return migrated


def migrate_schema_12(document):
    """Upgrade an immutable schema-12 payload with its legacy deployed pair."""
    validate_legacy_schema12_document(document)
    migrated = deepcopy(document)
    migrated["schema_version"] = DISK_SCHEMA_VERSION
    _add_legacy_active_drifter_ids(migrated)
    _add_carried_supply_defaults(migrated)
    _add_advancement_defaults(migrated)
    _add_permanent_discovery_defaults(migrated)
    _add_floor_two_defaults(migrated)
    _add_equipment_defaults(migrated)
    _validate_document(migrated, schema_version=DISK_SCHEMA_VERSION)
    return migrated


def migrate_schema_13(document):
    """Upgrade a schema-13 save with an empty carried-supplies pack."""
    validate_legacy_schema13_document(document)
    migrated = deepcopy(document)
    migrated["schema_version"] = DISK_SCHEMA_VERSION
    _add_carried_supply_defaults(migrated)
    _add_advancement_defaults(migrated)
    _add_permanent_discovery_defaults(migrated)
    _add_floor_two_defaults(migrated)
    _add_equipment_defaults(migrated)
    _validate_document(migrated, schema_version=DISK_SCHEMA_VERSION)
    return migrated


def migrate_schema14(document):
    """Upgrade an immutable schema-14 payload with empty M3 advancement state."""
    validate_legacy_schema14_document(document)
    migrated = deepcopy(document)
    migrated["schema_version"] = DISK_SCHEMA_VERSION
    _add_advancement_defaults(migrated)
    _add_permanent_discovery_defaults(migrated)
    _add_floor_two_defaults(migrated)
    _add_equipment_defaults(migrated)
    _validate_document(migrated, schema_version=DISK_SCHEMA_VERSION)
    return migrated


def migrate_schema15(document):
    """Upgrade schema-15 saves with empty permanent-discovery state."""
    validate_legacy_schema15_document(document)
    migrated = deepcopy(document)
    migrated["schema_version"] = DISK_SCHEMA_VERSION
    _add_permanent_discovery_defaults(migrated)
    _add_respec_defaults(migrated)
    _add_floor_two_defaults(migrated)
    _add_equipment_defaults(migrated)
    _validate_document(migrated, schema_version=DISK_SCHEMA_VERSION)
    return migrated


def migrate_schema16(document):
    """Add respec history to a schema-16 save without changing its input."""
    validate_legacy_schema16_document(document)
    migrated = deepcopy(document)
    migrated["schema_version"] = DISK_SCHEMA_VERSION
    _add_respec_defaults(migrated)
    _add_floor_two_defaults(migrated)
    _add_equipment_defaults(migrated)
    _validate_document(migrated, schema_version=DISK_SCHEMA_VERSION)
    return migrated


def migrate_schema17(document):
    """Add empty Floor II run-event state to an immutable schema-17 save."""
    validate_legacy_schema17_document(document)
    migrated = deepcopy(document)
    migrated["schema_version"] = DISK_SCHEMA_VERSION
    _add_floor_two_defaults(migrated)
    _add_equipment_defaults(migrated)
    _validate_document(migrated, schema_version=DISK_SCHEMA_VERSION)
    return migrated


def migrate_schema18(document):
    """Add empty equipment ownership state to an immutable schema-18 save."""
    validate_legacy_schema18_document(document)
    migrated = deepcopy(document)
    migrated["schema_version"] = DISK_SCHEMA_VERSION
    _add_equipment_defaults(migrated)
    _add_floor_three_defaults(migrated)
    _validate_document(migrated, schema_version=DISK_SCHEMA_VERSION)
    return migrated


def migrate_schema19(document):
    """Add rarity, modifier slots, and upgrade rank to M5 equipment."""
    validate_legacy_schema19_document(document)
    migrated = deepcopy(document)
    migrated["schema_version"] = DISK_SCHEMA_VERSION
    _add_armor_generation_defaults(migrated)
    _add_floor_three_defaults(migrated)
    _validate_document(migrated, schema_version=DISK_SCHEMA_VERSION)
    return migrated


def migrate_schema20(document):
    """Add empty loose-modifier ownership to an immutable schema-20 save."""
    validate_legacy_schema20_document(document)
    migrated = deepcopy(document)
    migrated["schema_version"] = DISK_SCHEMA_VERSION
    migrated["party"]["modifier_instances"] = []
    _add_floor_three_defaults(migrated)
    _validate_document(migrated, schema_version=DISK_SCHEMA_VERSION)
    return migrated


def migrate_schema21(document):
    """Add Floor III state defaults to schema-21 saves."""
    validate_legacy_schema21_document(document)
    migrated = deepcopy(document)
    migrated["schema_version"] = DISK_SCHEMA_VERSION
    _add_floor_three_defaults(migrated)
    _validate_document(migrated, schema_version=DISK_SCHEMA_VERSION)
    return migrated


def migrate_schema22(document):
    """Add Floor III state defaults to immutable schema-22 saves."""
    validate_legacy_schema22_document(document)
    migrated = deepcopy(document)
    migrated["schema_version"] = DISK_SCHEMA_VERSION
    _add_floor_three_defaults(migrated)
    _validate_document(migrated, schema_version=DISK_SCHEMA_VERSION)
    return migrated


def validate_legacy_schema9_document(document):
    """Validate and copy an immutable schema-9 profile payload."""
    _validate_legacy_current_document(document)
    return deepcopy(document)


def validate_legacy_schema10_document(document):
    """Validate and copy an immutable schema-10 profile payload."""
    _validate_document(
        document,
        schema_version=_PREVIOUS_CURRENT_DISK_SCHEMA_VERSION,
        require_signature_weapon=False,
    )
    return deepcopy(document)


def validate_legacy_schema11_document(document):
    """Validate and copy an immutable schema-11 profile payload."""
    _validate_plain_document(document)
    _require_mapping(document, "game")
    if document.get("schema_version") != _CURRENT_PREVIOUS_DISK_SCHEMA_VERSION:
        raise SaveStateValidationError("save schema version mismatch")
    historical = deepcopy(document)
    players = [historical.get("player")]
    party = historical.get("party")
    if isinstance(party, dict) and isinstance(party.get("companions"), list):
        players.extend(party["companions"])
    for player in players:
        weapon = player.get("signature_weapon") if isinstance(player, dict) else None
        if isinstance(weapon, dict) and "tier_v_success" in weapon:
            raise SaveStateValidationError(
                "schema-11 signature weapon cannot contain tier_v_success"
            )
    historical["schema_version"] = _PREVIOUS_DISK_SCHEMA_VERSION_CURRENT
    _add_tier_v_success_defaults(historical)
    _validate_document(
        historical,
        schema_version=_PREVIOUS_DISK_SCHEMA_VERSION_CURRENT,
    )
    historical["schema_version"] = DISK_SCHEMA_VERSION
    _add_legacy_active_drifter_ids(historical)
    _add_carried_supply_defaults(historical)
    _add_advancement_defaults(historical)
    _add_permanent_discovery_defaults(historical)
    _add_floor_two_defaults(historical)
    _add_equipment_defaults(historical)
    _validate_document(historical, schema_version=DISK_SCHEMA_VERSION)
    return deepcopy(document)


def validate_legacy_schema12_document(document):
    """Validate and copy an immutable schema-12 payload without migrating it."""
    _validate_plain_document(document)
    _validate_document(document, schema_version=_PREVIOUS_DISK_SCHEMA_VERSION_CURRENT)
    return deepcopy(document)


def validate_legacy_schema13_document(document):
    """Validate and copy an immutable schema-13 payload without migrating it."""
    _validate_plain_document(document)
    _validate_document(document, schema_version=_LATEST_PREVIOUS_DISK_SCHEMA_VERSION)
    return deepcopy(document)


def validate_legacy_schema14_document(document):
    """Validate and copy an immutable schema-14 payload without migrating it."""
    _validate_plain_document(document)
    _validate_document(
        document,
        schema_version=_PREVIOUS_CURRENT_DISK_SCHEMA_VERSION_CURRENT,
    )
    return deepcopy(document)


def validate_legacy_schema15_document(document):
    """Validate schema-15 profile history without mutating or upgrading it."""
    _validate_plain_document(document)
    _validate_document(
        document,
        schema_version=_LATEST_PREVIOUS_CURRENT_DISK_SCHEMA_VERSION_CURRENT,
    )
    return deepcopy(document)


def validate_legacy_schema16_document(document):
    """Validate schema-16 profile history without mutating or upgrading it."""
    _validate_plain_document(document)
    _validate_document(
        document,
        schema_version=_PRE_RESPEC_DISK_SCHEMA_VERSION,
    )
    return deepcopy(document)


def validate_legacy_schema17_document(document):
    """Validate schema-17 profile history without changing its shape."""
    _validate_plain_document(document)
    _validate_document(
        document,
        schema_version=_PRE_RUN_EVENT_DISK_SCHEMA_VERSION,
    )
    return deepcopy(document)


def validate_legacy_schema18_document(document):
    """Validate schema-18 profile history without changing its shape."""
    _validate_plain_document(document)
    _validate_document(
        document,
        schema_version=_PRE_EQUIPMENT_DISK_SCHEMA_VERSION,
    )
    return deepcopy(document)


def validate_legacy_schema19_document(document):
    """Validate immutable schema-19 equipment payloads without changing shape."""
    _validate_plain_document(document)
    _validate_document(
        document,
        schema_version=_PRE_GENERATED_EQUIPMENT_DISK_SCHEMA_VERSION,
    )
    return deepcopy(document)


def validate_legacy_schema20_document(document):
    """Validate immutable schema-20 equipment and event history."""
    _validate_plain_document(document)
    _validate_document(document, schema_version=_PRE_ALCHEMIST_DISK_SCHEMA_VERSION)
    return deepcopy(document)


def validate_legacy_schema21_document(document):
    """Validate immutable schema-21 saves without helper-selection events."""
    _validate_plain_document(document)
    _validate_document(document, schema_version=_PRE_BOSS_HELPER_DISK_SCHEMA_VERSION)
    return deepcopy(document)


def validate_legacy_schema22_document(document):
    """Validate immutable schema-22 saves without adding Floor III state."""
    _validate_plain_document(document)
    _validate_document(
        document,
        schema_version=_PRE_FLOOR_THREE_DISK_SCHEMA_VERSION,
    )
    return deepcopy(document)


def validate_legacy_schema8_document(document):
    """Validate and copy an original schema-8 disk payload without migrating it."""
    _validate_plain_document(document)
    _validate_legacy_schema8_document(document)
    return deepcopy(document)


def validate_profile_payload(document):
    """Validate current payloads or immutable schema-8 through schema-22 history."""
    if (
        isinstance(document, dict)
        and document.get("schema_version") == _LEGACY_DISK_SCHEMA_VERSION
        and "party" not in document
    ):
        return validate_legacy_schema8_document(document)
    if (
        isinstance(document, dict)
        and document.get("schema_version") == _PREVIOUS_DISK_SCHEMA_VERSION
    ):
        return validate_legacy_schema9_document(document)
    if (
        isinstance(document, dict)
        and document.get("schema_version")
        == _CURRENT_PREVIOUS_DISK_SCHEMA_VERSION
    ):
        return validate_legacy_schema11_document(document)
    if (
        isinstance(document, dict)
        and document.get("schema_version")
        == _PREVIOUS_DISK_SCHEMA_VERSION_CURRENT
    ):
        return validate_legacy_schema12_document(document)
    if (
        isinstance(document, dict)
        and document.get("schema_version") == _LATEST_PREVIOUS_DISK_SCHEMA_VERSION
    ):
        return validate_legacy_schema13_document(document)
    if (
        isinstance(document, dict)
        and document.get("schema_version")
        == _PREVIOUS_CURRENT_DISK_SCHEMA_VERSION_CURRENT
    ):
        return validate_legacy_schema14_document(document)
    if (
        isinstance(document, dict)
        and document.get("schema_version")
        == _LATEST_PREVIOUS_CURRENT_DISK_SCHEMA_VERSION_CURRENT
    ):
        return validate_legacy_schema15_document(document)
    if (
        isinstance(document, dict)
        and document.get("schema_version") == _PRE_RESPEC_DISK_SCHEMA_VERSION
    ):
        return validate_legacy_schema16_document(document)
    if (
        isinstance(document, dict)
        and document.get("schema_version") == _PRE_RUN_EVENT_DISK_SCHEMA_VERSION
    ):
        return validate_legacy_schema17_document(document)
    if (
        isinstance(document, dict)
        and document.get("schema_version") == _PRE_EQUIPMENT_DISK_SCHEMA_VERSION
    ):
        return validate_legacy_schema18_document(document)
    if (
        isinstance(document, dict)
        and document.get("schema_version")
        == _PRE_GENERATED_EQUIPMENT_DISK_SCHEMA_VERSION
    ):
        return validate_legacy_schema19_document(document)
    if (
        isinstance(document, dict)
        and document.get("schema_version") == _PRE_ALCHEMIST_DISK_SCHEMA_VERSION
    ):
        return validate_legacy_schema20_document(document)
    if (
        isinstance(document, dict)
        and document.get("schema_version") == _PRE_BOSS_HELPER_DISK_SCHEMA_VERSION
    ):
        return validate_legacy_schema21_document(document)
    if (
        isinstance(document, dict)
        and document.get("schema_version")
        == _PRE_FLOOR_THREE_DISK_SCHEMA_VERSION
    ):
        return validate_legacy_schema22_document(document)
    if (
        isinstance(document, dict)
        and document.get("schema_version") == _PREVIOUS_CURRENT_DISK_SCHEMA_VERSION
    ):
        return validate_legacy_schema10_document(document)
    normalized = validate_save_document(document)
    if normalized != document:
        raise SaveStateValidationError("profile payload is not canonical")
    return normalized


def reconstruct_game_state(document):
    source_schema_version = (
        document.get("schema_version") if isinstance(document, dict) else None
    )
    document = validate_save_document(document)

    try:
        profile = _canonical_profile(document["player"])
        character = profile.create_character()
        player = _reconstruct_player(character, document["player"])
        story = StoryState.from_snapshot(document["story"])
        world = WorldState.from_snapshot(document["world"])
        overworld = OverworldState.from_snapshot(document["overworld"])
        companions = tuple(
            _reconstruct_player(
                _canonical_profile(snapshot).create_character(),
                snapshot,
            )
            for snapshot in document["party"]["companions"]
        )
        party = PartyState.from_snapshot(
            document["party"],
            companions=companions,
            require_active_run_scope=(source_schema_version == DISK_SCHEMA_VERSION),
        )
        return GameState.from_persistent_parts(
            player,
            story,
            world,
            overworld,
            document["metadata"],
            party,
        )
    except (KeyError, TypeError, ValueError) as error:
        if isinstance(error, SaveStateValidationError):
            raise
        raise SaveStateValidationError(
            f"save reconstruction failed: {error}"
        ) from error


def validate_save_document(document):
    """Validate and normalize a legacy or current save document without loading it."""
    _validate_plain_document(document)
    schema_version = document.get("schema_version")
    if schema_version == _LEGACY_RUNTIME_SCHEMA_VERSION:
        return migrate_schema_7(document)
    if schema_version == _LEGACY_DISK_SCHEMA_VERSION:
        if "party" not in document:
            return migrate_schema_8(document)
        _validate_legacy_current_document(
            document,
            schema_version=_LEGACY_DISK_SCHEMA_VERSION,
        )
        return _migrate_previous_current_document(document)
    if schema_version == _PREVIOUS_DISK_SCHEMA_VERSION:
        return migrate_schema_9(document)
    if schema_version == _PREVIOUS_CURRENT_DISK_SCHEMA_VERSION:
        return migrate_schema_10(document)
    if schema_version == _CURRENT_PREVIOUS_DISK_SCHEMA_VERSION:
        return migrate_schema_11(document)
    if schema_version == _PREVIOUS_DISK_SCHEMA_VERSION_CURRENT:
        return migrate_schema_12(document)
    if schema_version == _LATEST_PREVIOUS_DISK_SCHEMA_VERSION:
        return migrate_schema_13(document)
    if schema_version == _PREVIOUS_CURRENT_DISK_SCHEMA_VERSION_CURRENT:
        return migrate_schema14(document)
    if schema_version == _LATEST_PREVIOUS_CURRENT_DISK_SCHEMA_VERSION_CURRENT:
        return migrate_schema15(document)
    if schema_version == _PRE_RESPEC_DISK_SCHEMA_VERSION:
        return migrate_schema16(document)
    if schema_version == _PRE_RUN_EVENT_DISK_SCHEMA_VERSION:
        return migrate_schema17(document)
    if schema_version == _PRE_EQUIPMENT_DISK_SCHEMA_VERSION:
        return migrate_schema18(document)
    if schema_version == _PRE_GENERATED_EQUIPMENT_DISK_SCHEMA_VERSION:
        return migrate_schema19(document)
    if schema_version == _PRE_ALCHEMIST_DISK_SCHEMA_VERSION:
        return migrate_schema20(document)
    if schema_version == _PRE_BOSS_HELPER_DISK_SCHEMA_VERSION:
        return migrate_schema21(document)
    if schema_version == _PRE_FLOOR_THREE_DISK_SCHEMA_VERSION:
        return migrate_schema22(document)
    if schema_version == DISK_SCHEMA_VERSION:
        normalized = deepcopy(document)
        if isinstance(normalized.get("player"), dict):
            normalized["player"].pop("combat", None)
        _strip_companion_combat(normalized.get("party"))
        _validate_document(
            normalized,
            schema_version=DISK_SCHEMA_VERSION,
            require_active_run_scope=True,
        )
        return normalized
    raise SaveStateValidationError(
        f"unsupported save schema: {schema_version!r}"
    )


def _reconstruct_player(character, snapshot):
    inventory_items = tuple(
        _reconstruct_item(item, "player.inventory")
        for item in snapshot["inventory"]
    )
    equipment_items = {
        slot: _reconstruct_equipment_item(item, f"player.equipment.{slot}")
        for slot, item in snapshot["equipment"].items()
    }
    run_state = snapshot["run_state"]
    checkpoint = CharacterRunCheckpoint(
        inventory=tuple(
            (RunItemId(item_id), quantity)
            for item_id, quantity in run_state["inventory"].items()
        ),
        prepared_payloads=tuple(
            (
                PreparedPayloadId(payload_id),
                None if infusion is None else InfusionKind(infusion),
            )
            for payload_id, infusion in run_state["prepared_payloads"].items()
        ),
    )
    return PlayerState.from_persistent_snapshot(
        character,
        snapshot,
        inventory_items=inventory_items,
        equipment_items=equipment_items,
        run_checkpoint=checkpoint,
    )


def _canonical_profile(player_snapshot):
    identity = player_snapshot["identity"]
    _require_mapping(identity, "player.identity")
    _require_exact_keys(
        identity,
        {"display_name", "full_display_name", "archetype_name", "profile"},
        "player.identity",
    )
    profile_data = identity["profile"]
    _require_mapping(profile_data, "player.identity.profile")
    _require_exact_keys(
        profile_data,
        {"choice", "short_name", "display_name"},
        "player.identity.profile",
    )
    if not isinstance(profile_data["choice"], str):
        raise SaveStateValidationError("profile choice must be a string")
    profile = get_drifter_spec_by_choice(profile_data["choice"])
    if profile is None:
        raise SaveStateValidationError(
            f"unknown character profile: {profile_data['choice']!r}"
        )
    if profile_data != {
        "choice": profile.choice,
        "short_name": profile.short_name,
        "display_name": profile.display_name,
    }:
        raise SaveStateValidationError("character profile identity is not canonical")
    character = profile.create_character()
    if identity["display_name"] != character.display_name:
        raise SaveStateValidationError("character display name is not canonical")
    if identity["full_display_name"] != character.full_display_name:
        raise SaveStateValidationError("character full display name is not canonical")
    if identity["archetype_name"] != character.archetype_name:
        raise SaveStateValidationError("character archetype is not canonical")
    return profile


def _reconstruct_item(item, path):
    if isinstance(item, dict):
        return _reconstruct_weapon(item, path)
    if isinstance(item, (str, bool, int, float)) or item is None:
        return item
    raise SaveStateValidationError(f"{path} contains an unsupported item")


def _reconstruct_equipment_item(item, path):
    if item is None:
        return None
    if not isinstance(item, dict):
        raise SaveStateValidationError(f"{path} must be a known weapon or null")
    return _reconstruct_weapon(item, path)


def _reconstruct_weapon(payload, path):
    weapon_type = payload.get("type")
    if not isinstance(weapon_type, str):
        raise SaveStateValidationError(f"{path}.type must be a known weapon type")
    try:
        weapon = create_weapon_from_persistence_key(weapon_type)
    except ValueError as error:
        raise SaveStateValidationError(
            f"{path} contains an unknown weapon type"
        ) from error

    if payload != _weapon_payload(weapon):
        raise SaveStateValidationError(f"{path} does not match authored weapon data")
    return weapon


def _weapon_payload(weapon):
    return {
        "type": weapon.persistence_key,
        "name": weapon.name,
        "weapon_type": weapon.weapon_type,
        "intended_wielder": weapon.intended_wielder,
        "stat_bonuses": weapon.stat_bonuses,
        "value": weapon.value,
        "description": weapon.description,
    }


def _validate_document(
    document,
    *,
    schema_version,
    require_signature_weapon=None,
    require_active_run_scope=False,
):
    allowed_keys = {
        "schema_version",
        "player",
        "story",
        "world",
        "overworld",
        "party",
        "metadata",
    }
    _require_mapping(document, "game")
    _require_exact_keys(document, allowed_keys, "game")
    if document["schema_version"] != schema_version:
        raise SaveStateValidationError("save schema version mismatch")
    if require_signature_weapon is None:
        require_signature_weapon = schema_version >= _PREVIOUS_DISK_SCHEMA_VERSION_CURRENT
    equipment_by_id = {}
    equipment_bonuses_by_member = None
    if schema_version >= _PRE_GENERATED_EQUIPMENT_DISK_SCHEMA_VERSION:
        raw_party = document.get("party")
        if not isinstance(raw_party, dict):
            raise SaveStateValidationError("game.party must be an object")
        equipment_by_id = _validate_equipment_instances(
            raw_party.get("equipment_instances"),
            require_generation_state=(
                schema_version >= _PRE_ALCHEMIST_DISK_SCHEMA_VERSION
            ),
        )
        equipment_bonuses_by_member = _validate_equipment_relationships(
            document["player"], raw_party, equipment_by_id
        )
    _validate_player(
        document["player"],
        require_signature_weapon=require_signature_weapon,
        require_advancement=(
            schema_version >= _LATEST_PREVIOUS_CURRENT_DISK_SCHEMA_VERSION_CURRENT
        ),
        require_respec_state=(
            schema_version >= _PRE_RUN_EVENT_DISK_SCHEMA_VERSION
        ),
        require_discovery_bonuses=(
            schema_version >= _PRE_RESPEC_DISK_SCHEMA_VERSION
        ),
        require_equipment_refs=(
            schema_version >= _PRE_GENERATED_EQUIPMENT_DISK_SCHEMA_VERSION
        ),
        equipment_stat_bonuses=(
            None
            if equipment_bonuses_by_member is None
            else equipment_bonuses_by_member[0]
        ),
    )
    _validate_story(document["story"])
    _validate_world(
        document["world"],
        require_permanent_discovery_claims=(
            schema_version >= _PRE_RESPEC_DISK_SCHEMA_VERSION
        ),
        require_discovered_permanent_discovery_sources=(
            schema_version >= _PRE_EQUIPMENT_DISK_SCHEMA_VERSION
        ),
        require_authored_discovery_sources=(
            schema_version >= _PRE_EQUIPMENT_DISK_SCHEMA_VERSION
        ),
    )
    _validate_overworld(
        document["overworld"],
        document["world"],
        allow_floor_three=schema_version >= DISK_SCHEMA_VERSION,
    )
    if schema_version < _PRE_ALCHEMIST_DISK_SCHEMA_VERSION and any(
        isinstance(event, dict) and event.get("kind") == "armor_reward"
        for event in document["party"].get("resolved_run_events", [])
    ):
        raise SaveStateValidationError(
            "legacy run history cannot contain M5 armor reward events"
        )
    if schema_version < DISK_SCHEMA_VERSION and any(
        isinstance(event, dict) and event.get("kind") == "boss_helper_selection"
        for event in document["party"].get("resolved_run_events", [])
    ):
        raise SaveStateValidationError(
            "legacy run history cannot contain boss-helper selection events"
        )
    equipment_by_id = _validate_party(
        document["party"],
        document["player"],
        require_signature_weapon=require_signature_weapon,
        require_advancement=(
            schema_version >= _LATEST_PREVIOUS_CURRENT_DISK_SCHEMA_VERSION_CURRENT
        ),
        require_respec_state=(
            schema_version >= _PRE_RUN_EVENT_DISK_SCHEMA_VERSION
        ),
        require_discovery_bonuses=(
            schema_version >= _PRE_RESPEC_DISK_SCHEMA_VERSION
        ),
        require_active_drifter_ids=(
            schema_version >= _LATEST_PREVIOUS_DISK_SCHEMA_VERSION
        ),
        require_carried_supplies=(
            schema_version >= _PREVIOUS_CURRENT_DISK_SCHEMA_VERSION_CURRENT
        ),
        require_floor_two_state=(
            schema_version >= _PRE_EQUIPMENT_DISK_SCHEMA_VERSION
        ),
        require_equipment_instances=(
            schema_version >= _PRE_GENERATED_EQUIPMENT_DISK_SCHEMA_VERSION
        ),
        require_generated_equipment_state=(
            schema_version >= _PRE_ALCHEMIST_DISK_SCHEMA_VERSION
        ),
        require_modifier_instances=(
            schema_version >= _PRE_BOSS_HELPER_DISK_SCHEMA_VERSION
        ),
        require_floor_three_state=(schema_version >= DISK_SCHEMA_VERSION),
        require_active_run_scope=require_active_run_scope,
        equipment_by_id=equipment_by_id,
        equipment_bonuses_by_member=(
            None
            if equipment_bonuses_by_member is None
            else equipment_bonuses_by_member[1:]
        ),
    )
    _validate_route_party_relationship(
        document["overworld"],
        document["party"],
        require_floor_three_state=(schema_version >= DISK_SCHEMA_VERSION),
    )
    if schema_version >= _PRE_ALCHEMIST_DISK_SCHEMA_VERSION:
        _validate_armor_reward_event_relationship(
            document["party"], equipment_by_id
        )
    if schema_version >= _PRE_EQUIPMENT_DISK_SCHEMA_VERSION:
        _validate_discovery_event_world_relationship(
            document["world"], document["party"]
        )
    validate_plain_value(document["metadata"], "game.metadata")


def _validate_legacy_current_document(
    document,
    *,
    schema_version=_PREVIOUS_DISK_SCHEMA_VERSION,
):
    _validate_plain_document(document)
    allowed_keys = {
        "schema_version",
        "player",
        "story",
        "world",
        "overworld",
        "party",
        "metadata",
    }
    _require_mapping(document, "game")
    _require_exact_keys(document, allowed_keys, "game")
    if document["schema_version"] != schema_version:
        raise SaveStateValidationError("save schema version mismatch")
    _validate_player(document["player"], require_signature_weapon=False)
    _validate_story(document["story"])
    _validate_world(document["world"])
    _validate_legacy_overworld(document["overworld"], document["world"])
    _validate_legacy_party(document["party"], document["player"])
    at_dungeon_entrance = (
        document["overworld"]["current_route_node_id"]
        == _DUNGEON_ENTRANCE_NODE_ID
    )
    if at_dungeon_entrance != (
        document["party"]["phase"] != DungeonPhase.OUTSIDE.value
    ):
        raise SaveStateValidationError(
            "dungeon entrance and party phase are inconsistent"
        )
    validate_plain_value(document["metadata"], "game.metadata")


def _migrate_previous_current_document(document):
    migrated = deepcopy(document)
    migrated["schema_version"] = DISK_SCHEMA_VERSION
    migrated["overworld"].setdefault("active_route_id", "surface")
    migrated["party"].setdefault("floor_one_cleared", False)
    migrated["party"].setdefault("floor_one_runs_started_after_clear", 0)
    migrated["party"].setdefault("outing_xp_multiplier_percent", 100)
    migrated["party"].setdefault("crafting_experience", 0)
    _add_carried_supply_defaults(migrated)
    if isinstance(migrated.get("player"), dict):
        migrated["player"].pop("combat", None)
    _strip_companion_combat(migrated.get("party"))
    _add_signature_weapon_defaults(migrated)
    _add_tier_v_success_defaults(migrated)
    _add_legacy_active_drifter_ids(migrated)
    _add_advancement_defaults(migrated)
    _add_permanent_discovery_defaults(migrated)
    _add_floor_two_defaults(migrated)
    _add_equipment_defaults(migrated)
    _validate_document(migrated, schema_version=DISK_SCHEMA_VERSION)
    return migrated


def _add_legacy_active_drifter_ids(document):
    party = document.get("party")
    if not isinstance(party, dict) or "active_drifter_ids" in party:
        return
    player = document.get("player")
    if not isinstance(player, dict):
        raise SaveStateValidationError("game.player must be an object")
    active_ids = [_canonical_profile(player).drifter_id]
    companions = party.get("companions")
    if not isinstance(companions, list):
        raise SaveStateValidationError("party.companions must be a list")
    if companions:
        active_ids.append(_canonical_profile(companions[0]).drifter_id)
    party["active_drifter_ids"] = active_ids


def _add_signature_weapon_defaults(document):
    players = [document.get("player")]
    party = document.get("party")
    if isinstance(party, dict) and isinstance(party.get("companions"), list):
        players.extend(party["companions"])
    for player in players:
        if not isinstance(player, dict) or "signature_weapon" in player:
            continue
        weapon_snapshot = player.get("equipment", {}).get("weapon")
        if not isinstance(weapon_snapshot, dict):
            raise SaveStateValidationError(
                "legacy Drifter is missing its signature weapon"
            )
        try:
            weapon = create_weapon_from_persistence_key(
                weapon_snapshot["type"]
            )
            progression = get_weapon_spec(weapon.item_id).progression
        except (KeyError, TypeError, ValueError) as error:
            raise SaveStateValidationError(
                "legacy Drifter has an invalid signature weapon"
            ) from error
        if progression is None:
            raise SaveStateValidationError(
                "legacy signature weapon progression is missing"
            )
        player["signature_weapon"] = {
            "weapon_id": weapon.item_id,
            "components": {
                slot.slot_id: slot.starting_component_id
                for slot in progression.slots
            },
            "slot_progress": {
                slot.slot_id: 0 for slot in progression.slots
            },
            "learned_technique_ids": [],
            "tier_v_success": False,
        }


def _add_tier_v_success_defaults(document):
    players = [document.get("player")]
    party = document.get("party")
    if isinstance(party, dict) and isinstance(party.get("companions"), list):
        players.extend(party["companions"])
    for player in players:
        if not isinstance(player, dict):
            continue
        weapon = player.get("signature_weapon")
        if isinstance(weapon, dict):
            weapon.setdefault("tier_v_success", False)


def _validate_legacy_schema8_document(document):
    allowed_keys = {
        "schema_version",
        "player",
        "story",
        "world",
        "overworld",
        "metadata",
    }
    _require_mapping(document, "game")
    _require_exact_keys(document, allowed_keys, "game")
    if document["schema_version"] != _LEGACY_DISK_SCHEMA_VERSION:
        raise SaveStateValidationError("save schema version mismatch")
    _validate_player(document["player"], require_signature_weapon=False)
    _validate_story(document["story"])
    _validate_world(document["world"])
    _validate_legacy_overworld(document["overworld"], document["world"])
    validate_plain_value(document["metadata"], "game.metadata")


def _validate_legacy_party(party, player):
    _require_mapping(party, "party")
    _require_exact_keys(
        party,
        {
            "companions",
            "shared_gold",
            "shared_items",
            "tutorial_complete",
            "phase",
            "outing_rewards",
        },
        "party",
    )
    if not isinstance(party["companions"], list) or len(party["companions"]) > 1:
        raise SaveStateValidationError("party.companions must contain at most one Drifter")
    lead_profile = _canonical_profile(player)
    companion_ids = set()
    for index, companion in enumerate(party["companions"]):
        _validate_player(companion, require_signature_weapon=False)
        choice = _canonical_profile(companion).choice
        if choice == lead_profile.choice or choice in companion_ids:
            raise SaveStateValidationError("party contains a duplicate Drifter")
        companion_ids.add(choice)

    _require_int_min(party["shared_gold"], 0, "party.shared_gold")
    _validate_item_stacks(party["shared_items"], "party.shared_items")
    if not isinstance(party["tutorial_complete"], bool):
        raise SaveStateValidationError("party.tutorial_complete must be a boolean")
    try:
        phase = DungeonPhase(party["phase"])
    except (TypeError, ValueError) as error:
        raise SaveStateValidationError("party.phase is invalid") from error
    if phase is DungeonPhase.COMPLETE:
        raise SaveStateValidationError(
            "complete party phase is not supported by this save schema"
        )

    rewards = party["outing_rewards"]
    _require_mapping(rewards, "party.outing_rewards")
    _require_exact_keys(rewards, {"experience", "gold", "items"}, "party.outing_rewards")
    _require_int_min(rewards["experience"], 0, "party.outing_rewards.experience")
    _require_int_min(rewards["gold"], 0, "party.outing_rewards.gold")
    _validate_item_stacks(rewards["items"], "party.outing_rewards.items")
    has_pending_rewards = bool(
        rewards["experience"] or rewards["gold"] or rewards["items"]
    )
    has_companion = bool(party["companions"])
    if phase is DungeonPhase.OUTING:
        raise SaveStateValidationError(
            "outing cannot be saved without a battle snapshot"
        )
    if phase is DungeonPhase.OUTSIDE and (
        has_companion
        or party["shared_gold"]
        or party["tutorial_complete"]
        or has_pending_rewards
    ):
        raise SaveStateValidationError("outside party state contains dungeon progress")
    if phase in {DungeonPhase.PARTY_READY, DungeonPhase.OUTING, DungeonPhase.EXTRACTION} and not has_companion:
        raise SaveStateValidationError("active dungeon phase requires a companion")
    if phase in {DungeonPhase.HUB, DungeonPhase.PARTY_READY} and has_pending_rewards:
        raise SaveStateValidationError("pending rewards require an outing or extraction phase")
    if party["tutorial_complete"] and phase is not DungeonPhase.HUB:
        raise SaveStateValidationError("completed tutorial must be at the hub")
    if phase is DungeonPhase.HUB and (
        has_companion != party["tutorial_complete"]
    ):
        raise SaveStateValidationError(
            "hub party membership must match tutorial completion"
        )
    if phase is DungeonPhase.EXTRACTION and (
        rewards["experience"] % (1 + len(party["companions"]))
    ):
        raise SaveStateValidationError(
            "outing experience must divide evenly across the party"
        )


def _validate_party(
    party,
    player,
    *,
    require_signature_weapon=True,
    require_advancement=False,
    require_respec_state=False,
    require_discovery_bonuses=False,
    require_active_drifter_ids=False,
    require_carried_supplies=False,
    require_floor_two_state=False,
    require_floor_three_state=False,
    require_active_run_scope=False,
    require_equipment_instances=False,
    require_generated_equipment_state=False,
    require_modifier_instances=False,
    equipment_by_id=None,
    equipment_bonuses_by_member=None,
):
    _require_mapping(party, "party")
    expected_keys = {
        "companions",
        "shared_gold",
        "shared_items",
        "tutorial_complete",
        "phase",
        "outing_rewards",
        "floor_one_cleared",
        "floor_one_runs_started_after_clear",
        "outing_xp_multiplier_percent",
        "crafting_experience",
    }
    if require_active_drifter_ids:
        expected_keys.add("active_drifter_ids")
    if require_carried_supplies:
        expected_keys.add("carried_items")
    if require_floor_two_state:
        expected_keys.update(
            {
                "floor_two_cleared",
                "floor_two_runs_started_after_clear",
                "floor_two_run_id",
                "floor_two_outing_xp_multiplier_percent",
                "resolved_run_events",
            }
        )
    if require_floor_three_state:
        expected_keys.update(
            {
                "floor_three_cleared",
                "floor_three_runs_started_after_clear",
                "floor_three_run_id",
                "floor_three_outing_xp_multiplier_percent",
            }
        )
    if require_equipment_instances:
        expected_keys.add("equipment_instances")
    if require_modifier_instances:
        expected_keys.add("modifier_instances")
    _require_exact_keys(party, expected_keys, "party")
    if require_equipment_instances and equipment_by_id is None:
        equipment_by_id = _validate_equipment_instances(
            party["equipment_instances"],
            require_generation_state=require_generated_equipment_state,
        )
    if equipment_by_id is None:
        equipment_by_id = {}
    if require_modifier_instances:
        modifier_by_id = _validate_modifier_instances(party["modifier_instances"])
        if set(modifier_by_id) & set(equipment_by_id):
            raise SaveStateValidationError(
                "modifier and equipment instance IDs must be unique"
            )
    companions = party["companions"]
    max_companions = 3 if require_active_drifter_ids else 1
    if not isinstance(companions, list) or len(companions) > max_companions:
        raise SaveStateValidationError(
            f"party.companions must contain at most {max_companions} Drifters"
        )
    lead_profile = _canonical_profile(player)
    companion_ids = set()
    for index, companion in enumerate(companions):
        _validate_player(
            companion,
            require_signature_weapon=require_signature_weapon,
            require_advancement=require_advancement,
            require_respec_state=require_respec_state,
            require_discovery_bonuses=require_discovery_bonuses,
            require_equipment_refs=require_equipment_instances,
            equipment_stat_bonuses=(
                None
                if equipment_bonuses_by_member is None
                else equipment_bonuses_by_member[index]
            ),
        )
        choice = _canonical_profile(companion).choice
        if choice == lead_profile.choice or choice in companion_ids:
            raise SaveStateValidationError("party contains a duplicate Drifter")
        companion_ids.add(choice)

    active_ids = None
    if require_active_drifter_ids:
        active_ids = party["active_drifter_ids"]
        if not isinstance(active_ids, list) or len(active_ids) not in {1, 2}:
            raise SaveStateValidationError(
                "party.active_drifter_ids must contain one or two Drifters"
            )
        if any(not isinstance(value, str) or not value for value in active_ids):
            raise SaveStateValidationError(
                "party.active_drifter_ids must contain canonical IDs"
            )
        if len(active_ids) != len(set(active_ids)):
            raise SaveStateValidationError(
                "party.active_drifter_ids must not contain duplicates"
            )
        player_id = lead_profile.drifter_id
        recruited_ids = {player_id}
        recruited_ids.update(
            _canonical_profile(companion).drifter_id
            for companion in companions
        )
        if any(drifter_id not in recruited_ids for drifter_id in active_ids):
            raise SaveStateValidationError(
                "party.active_drifter_ids must refer to recruited Drifters"
            )
        expected_active_count = 2 if companions else 1
        if len(active_ids) != expected_active_count:
            raise SaveStateValidationError(
                "party.active_drifter_ids size disagrees with recruited roster"
            )
        if not companions and active_ids != [player_id]:
            raise SaveStateValidationError(
                "a solo roster must actively deploy its starting Drifter"
            )

    _require_int_min(party["shared_gold"], 0, "party.shared_gold")
    _validate_item_stacks(party["shared_items"], "party.shared_items")
    if require_carried_supplies:
        _validate_item_stacks(party["carried_items"], "party.carried_items")
        if any(
            (spec := get_supply_item(item_id)) is None or not spec.carryable
            for item_id in party["carried_items"]
        ):
            raise SaveStateValidationError(
                "party.carried_items contains an invalid carried item"
            )
        if sum(party["carried_items"].values()) > 6:
            raise SaveStateValidationError(
                "party.carried_items exceed the six-unit capacity"
            )
    _require_int_range(
        party["crafting_experience"],
        0,
        MAX_CRAFTING_EXPERIENCE,
        "party.crafting_experience",
    )
    if not isinstance(party["tutorial_complete"], bool):
        raise SaveStateValidationError(
            "party.tutorial_complete must be a boolean"
        )
    try:
        phase = DungeonPhase(party["phase"])
    except (TypeError, ValueError) as error:
        raise SaveStateValidationError("party.phase is invalid") from error
    if phase is DungeonPhase.COMPLETE:
        raise SaveStateValidationError(
            "complete party phase is not supported by this save schema"
        )

    rewards = party["outing_rewards"]
    _require_mapping(rewards, "party.outing_rewards")
    _require_exact_keys(
        rewards,
        {"experience", "gold", "items"},
        "party.outing_rewards",
    )
    _require_int_min(rewards["experience"], 0, "party.outing_rewards.experience")
    _require_int_min(rewards["gold"], 0, "party.outing_rewards.gold")
    _validate_item_stacks(rewards["items"], "party.outing_rewards.items")
    has_pending_rewards = bool(
        rewards["experience"] or rewards["gold"] or rewards["items"]
    )
    has_companion = bool(companions)
    if phase is DungeonPhase.OUTSIDE and (
        has_companion
        or party["shared_gold"]
        or party["tutorial_complete"]
        or has_pending_rewards
    ):
        raise SaveStateValidationError(
            "outside party state contains dungeon progress"
        )
    if phase in {
        DungeonPhase.PARTY_READY,
        DungeonPhase.OUTING,
        DungeonPhase.EXTRACTION,
    } and not has_companion:
        raise SaveStateValidationError(
            "active dungeon phase requires a companion"
        )
    if phase in {DungeonPhase.HUB, DungeonPhase.PARTY_READY} and has_pending_rewards:
        raise SaveStateValidationError(
            "pending rewards require an outing or extraction phase"
        )
    if phase is DungeonPhase.HUB and (
        has_companion != party["tutorial_complete"]
    ):
        raise SaveStateValidationError(
            "hub party membership must match tutorial completion"
        )
    reward_party_size = (
        len(active_ids) if active_ids is not None else 1 + len(companions)
    )
    if phase is DungeonPhase.EXTRACTION and rewards["experience"] % reward_party_size:
        raise SaveStateValidationError(
            "outing experience must divide evenly across the party"
        )

    cleared = party["floor_one_cleared"]
    if not isinstance(cleared, bool):
        raise SaveStateValidationError("party.floor_one_cleared must be a boolean")
    if cleared and not party["tutorial_complete"]:
        raise SaveStateValidationError(
            "Floor 1 cannot be cleared before the tutorial is complete"
        )
    _require_int_min(
        party["floor_one_runs_started_after_clear"],
        0,
        "party.floor_one_runs_started_after_clear",
    )
    runs_started = party["floor_one_runs_started_after_clear"]
    if runs_started and not cleared:
        raise SaveStateValidationError(
            "Floor 1 replay runs require a cleared floor"
        )
    _require_int_min(
        party["outing_xp_multiplier_percent"],
        0,
        "party.outing_xp_multiplier_percent",
    )
    multiplier = party["outing_xp_multiplier_percent"]
    if multiplier not in {20, 30, 40, 50, 100}:
        raise SaveStateValidationError(
            "party outing XP multiplier is not an authored rate"
        )
    active_floor_one = (
        party["tutorial_complete"]
        and phase is DungeonPhase.OUTING
        and (
            not require_floor_two_state
            or party["floor_two_run_id"] is None
        )
        and (
            not require_floor_three_state
            or party["floor_three_run_id"] is None
        )
    )
    if active_floor_one:
        expected_rate = 100
        if cleared:
            if runs_started < 1:
                raise SaveStateValidationError(
                    "a Floor 1 replay requires a started replay count"
                )
            expected_rate = (50, 40, 30, 20)[min(runs_started - 1, 3)]
        if multiplier != expected_rate:
            raise SaveStateValidationError(
                "active Floor 1 run has an inconsistent XP rate"
            )
    elif multiplier != 100:
        raise SaveStateValidationError(
            "inactive Floor 1 runs must use the default XP rate"
        )

    if require_floor_two_state:
        floor_two_cleared = party["floor_two_cleared"]
        if not isinstance(floor_two_cleared, bool):
            raise SaveStateValidationError(
                "party.floor_two_cleared must be a boolean"
            )
        if floor_two_cleared and not cleared:
            raise SaveStateValidationError(
                "Floor 2 cannot be cleared before Floor 1"
            )
        floor_two_runs = party["floor_two_runs_started_after_clear"]
        _require_int_min(
            floor_two_runs,
            0,
            "party.floor_two_runs_started_after_clear",
        )
        if floor_two_runs and not floor_two_cleared:
            raise SaveStateValidationError(
                "Floor 2 replay runs require a cleared floor"
            )

        run_id = party["floor_two_run_id"]
        if run_id is not None and not _valid_persisted_run_id(run_id):
            raise SaveStateValidationError("party.floor_two_run_id is invalid")
        floor_two_multiplier = party[
            "floor_two_outing_xp_multiplier_percent"
        ]
        _require_int_min(
            floor_two_multiplier,
            0,
            "party.floor_two_outing_xp_multiplier_percent",
        )
        if floor_two_multiplier not in {20, 30, 40, 50, 100}:
            raise SaveStateValidationError(
                "Floor 2 outing XP multiplier is not an authored rate"
            )

        events = party["resolved_run_events"]
        if not isinstance(events, list):
            raise SaveStateValidationError(
                "party.resolved_run_events must be a list"
            )
        try:
            active_run_id = (
                party["floor_three_run_id"]
                if require_floor_three_state
                and party["floor_three_run_id"] is not None
                else run_id
            )
            active_floor_id = (
                "floor_three"
                if require_floor_three_state
                and party["floor_three_run_id"] is not None
                else "floor_two"
            )
            validate_run_event_history(
                events,
                active_drifter_ids=active_ids,
                active_run_id=active_run_id,
                active_floor_id=active_floor_id,
                require_active_run_scope=require_active_run_scope,
            )
        except (TypeError, ValueError) as error:
            raise SaveStateValidationError(
                f"party.resolved_run_events is invalid: {error}"
            ) from error

        active_floor_two = run_id is not None
        if active_floor_two:
            if not cleared or not party["tutorial_complete"]:
                raise SaveStateValidationError(
                    "Floor 2 run requires a completed Floor 1"
                )
            if phase not in {DungeonPhase.OUTING, DungeonPhase.EXTRACTION}:
                raise SaveStateValidationError(
                    "active Floor 2 run must be an outing or extraction"
                )
            expected_floor_two_rate = 100
            if floor_two_cleared:
                if floor_two_runs < 1:
                    raise SaveStateValidationError(
                        "Floor 2 replay requires a started replay count"
                    )
                expected_floor_two_rate = (50, 40, 30, 20)[
                    min(floor_two_runs - 1, 3)
                ]
            if floor_two_multiplier != expected_floor_two_rate:
                raise SaveStateValidationError(
                    "active Floor 2 run has an inconsistent XP rate"
                )
        elif floor_two_multiplier != 100:
            raise SaveStateValidationError(
                "inactive Floor 2 runs must use the default XP rate"
            )

    if require_floor_three_state:
        floor_three_cleared = party["floor_three_cleared"]
        if not isinstance(floor_three_cleared, bool):
            raise SaveStateValidationError(
                "party.floor_three_cleared must be a boolean"
            )
        if floor_three_cleared and not party["floor_two_cleared"]:
            raise SaveStateValidationError(
                "Floor 3 cannot be cleared before Floor 2"
            )
        floor_three_runs = party["floor_three_runs_started_after_clear"]
        _require_int_min(
            floor_three_runs,
            0,
            "party.floor_three_runs_started_after_clear",
        )
        if floor_three_runs and not floor_three_cleared:
            raise SaveStateValidationError(
                "Floor 3 replay runs require a cleared floor"
            )
        floor_three_run_id = party["floor_three_run_id"]
        if floor_three_run_id is not None and not _valid_persisted_run_id(
            floor_three_run_id
        ):
            raise SaveStateValidationError(
                "party.floor_three_run_id is invalid"
            )
        if floor_three_run_id is not None and party["floor_two_run_id"] is not None:
            raise SaveStateValidationError(
                "only one dungeon floor may be active"
            )
        floor_three_multiplier = party[
            "floor_three_outing_xp_multiplier_percent"
        ]
        _require_int_min(
            floor_three_multiplier,
            0,
            "party.floor_three_outing_xp_multiplier_percent",
        )
        if floor_three_multiplier not in {20, 30, 40, 50, 100}:
            raise SaveStateValidationError(
                "Floor 3 outing XP multiplier is not an authored rate"
            )
        if floor_three_run_id is not None:
            if (
                not party["floor_two_cleared"]
                or not party["tutorial_complete"]
                or len(companions) != 3
            ):
                raise SaveStateValidationError(
                    "Floor 3 run requires a cleared Floor 2 and four recruited Drifters"
                )
            if phase not in {DungeonPhase.OUTING, DungeonPhase.EXTRACTION}:
                raise SaveStateValidationError(
                    "active Floor 3 run must be an outing or extraction"
                )
            expected_floor_three_rate = 100
            if floor_three_cleared:
                if floor_three_runs < 1:
                    raise SaveStateValidationError(
                        "Floor 3 replay requires a started replay count"
                    )
                expected_floor_three_rate = (50, 40, 30, 20)[
                    min(floor_three_runs - 1, 3)
                ]
            if floor_three_multiplier != expected_floor_three_rate:
                raise SaveStateValidationError(
                    "active Floor 3 run has an inconsistent XP rate"
                )
        elif floor_three_multiplier != 100:
            raise SaveStateValidationError(
                "inactive Floor 3 runs must use the default XP rate"
            )

    return equipment_by_id


def _valid_persisted_run_id(value):
    return (
        isinstance(value, str)
        and 1 <= len(value) <= 80
        and ("a" <= value[0] <= "z" or "0" <= value[0] <= "9")
        and all(
            "a" <= character <= "z"
            or "0" <= character <= "9"
            or character in "-_"
            for character in value
        )
    )


def _validate_item_stacks(items, path):
    _require_mapping(items, path)
    for item_id, quantity in items.items():
        if not isinstance(item_id, str) or not item_id:
            raise SaveStateValidationError(f"{path} contains an invalid item ID")
        _require_int_min(quantity, 1, f"{path}.{item_id}")


def _validate_equipment_references(references, path):
    _require_mapping(references, path)
    expected_slots = set(PlayerState.EQUIPMENT_REFERENCE_SLOTS)
    _require_exact_keys(references, expected_slots, path)
    for slot, instance_id in references.items():
        if instance_id is None:
            continue
        if not isinstance(instance_id, str):
            raise SaveStateValidationError(
                f"{path}.{slot} must be a canonical equipment UUID or null"
            )
        try:
            canonical_id = str(UUID(instance_id))
        except (TypeError, ValueError, AttributeError) as error:
            raise SaveStateValidationError(
                f"{path}.{slot} must be a canonical equipment UUID or null"
            ) from error
        if canonical_id != instance_id:
            raise SaveStateValidationError(
                f"{path}.{slot} must be a canonical equipment UUID or null"
            )


def _validate_equipment_instances(instances, *, require_generation_state=True):
    if not isinstance(instances, list):
        raise SaveStateValidationError("party.equipment_instances must be a list")
    by_id = {}
    for index, snapshot in enumerate(instances):
        try:
            if not require_generation_state and isinstance(snapshot, dict):
                historical_keys = {
                    "instance_id",
                    "definition_id",
                    "source_id",
                    "secured",
                    "stat_bonuses",
                }
                if set(snapshot) != historical_keys:
                    raise ValueError(
                        "schema-19 equipment instance has an invalid shape"
                    )
                snapshot = deepcopy(snapshot)
                template = get_equipment_template(snapshot.get("definition_id"))
                snapshot["rarity"] = "common" if template.is_armor else None
                snapshot["upgrade_rank"] = 0
                snapshot["modifier_slots"] = {}
            instance = EquipmentInstance.from_snapshot(snapshot)
        except (TypeError, ValueError, KeyError) as error:
            raise SaveStateValidationError(
                f"party.equipment_instances[{index}] is invalid: {error}"
            ) from error
        if instance.instance_id in by_id:
            raise SaveStateValidationError(
                "party.equipment_instances IDs must be unique"
            )
        by_id[instance.instance_id] = instance
    return by_id


def _validate_modifier_instances(instances):
    if not isinstance(instances, list):
        raise SaveStateValidationError("party.modifier_instances must be a list")
    by_id = {}
    for index, snapshot in enumerate(instances):
        try:
            instance = ArmorModifierInstance.from_snapshot(snapshot)
        except (TypeError, ValueError, KeyError) as error:
            raise SaveStateValidationError(
                f"party.modifier_instances[{index}] is invalid: {error}"
            ) from error
        if instance.instance_id in by_id:
            raise SaveStateValidationError(
                "party.modifier_instances IDs must be unique"
            )
        by_id[instance.instance_id] = instance
    return by_id


def _validate_equipment_relationships(player, party, equipment_by_id):
    companions = party.get("companions")
    if not isinstance(companions, list):
        raise SaveStateValidationError("party.companions must be a list")
    members = [player] + companions
    referenced_ids = set()
    member_bonuses = []
    for member_index, member in enumerate(members):
        if not isinstance(member, dict):
            raise SaveStateValidationError("party contains an invalid Drifter")
        path = "player.equipment_refs" if member_index == 0 else (
            f"party.companions[{member_index - 1}].equipment_refs"
        )
        references = member.get("equipment_refs")
        _validate_equipment_references(references, path)
        bonuses = {}
        for slot, instance_id in references.items():
            if instance_id is None:
                continue
            instance = equipment_by_id.get(instance_id)
            if instance is None:
                raise SaveStateValidationError(
                    f"{path}.{slot} refers to an unowned equipment instance"
                )
            if instance_id in referenced_ids:
                raise SaveStateValidationError(
                    "equipment instance cannot be referenced more than once"
                )
            if instance.slot_id != slot:
                raise SaveStateValidationError(
                    f"{path}.{slot} references equipment for another slot"
                )
            referenced_ids.add(instance_id)
            for stat, value in instance.stat_bonuses.items():
                bonuses[stat] = bonuses.get(stat, 0) + value
        member_bonuses.append(bonuses)
    return tuple(member_bonuses)


def _validate_armor_reward_event_relationship(party, equipment_by_id):
    events = party.get("resolved_run_events")
    if not isinstance(events, list):
        return
    rewarded_instances = set()
    for event in events:
        if event.get("kind") != "armor_reward":
            continue
        snapshot = event["result"]["instance"]
        instance_id = snapshot["instance_id"]
        if instance_id in rewarded_instances:
            raise SaveStateValidationError(
                "armor reward events cannot award the same instance twice"
            )
        rewarded_instances.add(instance_id)
        instance = equipment_by_id.get(instance_id)
        if instance is None:
            raise SaveStateValidationError(
                "armor reward event instance is not owned by the party"
            )
        current_snapshot = instance.snapshot()
        expected_snapshot = dict(snapshot)
        # Reward evidence records acquisition-time security; Rest can later secure it.
        expected_snapshot["secured"] = current_snapshot["secured"]
        if current_snapshot != expected_snapshot:
            raise SaveStateValidationError(
                "armor reward event outcome disagrees with its owned instance"
            )


def _add_legacy_party_state(document):
    player = document.get("player")
    if not isinstance(player, dict):
        raise SaveStateValidationError("game.player must be an object")
    overworld = document.get("overworld")
    at_dungeon_entrance = (
        isinstance(overworld, dict)
        and overworld.get("current_route_node_id") == _DUNGEON_ENTRANCE_NODE_ID
    )
    shared_gold = 0
    phase = DungeonPhase.OUTSIDE.value
    if at_dungeon_entrance:
        shared_gold = player["gold"]
        player["gold"] = 0
        phase = DungeonPhase.HUB.value
    document["party"] = {
        "companions": [],
        "shared_gold": shared_gold,
        "shared_items": {},
        "carried_items": {},
        "tutorial_complete": False,
        "phase": phase,
        "outing_rewards": {"experience": 0, "gold": 0, "items": {}},
        "floor_one_cleared": False,
        "floor_one_runs_started_after_clear": 0,
        "outing_xp_multiplier_percent": 100,
        "crafting_experience": 0,
    }


def _add_carried_supply_defaults(document):
    party = document.get("party")
    if isinstance(party, dict):
        party.setdefault("carried_items", {})


def _add_advancement_defaults(document):
    players = [document.get("player")]
    party = document.get("party")
    if isinstance(party, dict) and isinstance(party.get("companions"), list):
        players.extend(party["companions"])
    for player in players:
        if not isinstance(player, dict):
            raise SaveStateValidationError("legacy Drifter is invalid")
        if "advancement" in player:
            raise SaveStateValidationError(
                "legacy Drifter already contains M3 advancement state"
            )
        profile = _canonical_profile(player)
        normal_move_ids, super_move_ids = move_ids_for_kit(
            profile.drifter_id,
            profile.combat_moves,
        )
        player["advancement"] = AdvancementState(
            profile.drifter_id,
            normal_move_ids,
            super_move_ids,
        ).snapshot()


def _add_respec_defaults(document):
    players = [document.get("player")]
    party = document.get("party")
    if isinstance(party, dict) and isinstance(party.get("companions"), list):
        players.extend(party["companions"])
    for player in players:
        if not isinstance(player, dict):
            raise SaveStateValidationError("legacy Drifter is invalid")
        advancement = player.get("advancement")
        if not isinstance(advancement, dict):
            raise SaveStateValidationError("legacy advancement state is invalid")
        if "purchased_stat_points" in advancement or "respec_count" in advancement:
            raise SaveStateValidationError(
                "legacy Drifter already contains respec history"
            )
        advancement["purchased_stat_points"] = {
            name: 0 for name in PermanentStats.STAT_NAMES
        }
        advancement["respec_count"] = 0


def _add_permanent_discovery_defaults(document):
    players = [document.get("player")]
    party = document.get("party")
    if isinstance(party, dict) and isinstance(party.get("companions"), list):
        players.extend(party["companions"])
    for player in players:
        if not isinstance(player, dict):
            raise SaveStateValidationError("legacy Drifter is invalid")
        if "permanent_discovery_bonuses" in player:
            raise SaveStateValidationError(
                "legacy Drifter already contains permanent-discovery bonuses"
            )
        player["permanent_discovery_bonuses"] = {
            "max_hp": 0,
            "max_mana": 0,
            "growth_points_awarded": 0,
        }
    world = document.get("world")
    if not isinstance(world, dict):
        raise SaveStateValidationError("game.world must be an object")
    existing_claims = world.get("permanent_discovery_claims", [])
    if existing_claims != []:
        raise SaveStateValidationError(
            "legacy world already contains permanent-discovery claims"
        )
    world["permanent_discovery_claims"] = []


def _add_floor_two_defaults(document):
    party = document.get("party")
    world = document.get("world")
    if not isinstance(party, dict):
        raise SaveStateValidationError("game.party must be an object")
    if not isinstance(world, dict):
        raise SaveStateValidationError("game.world must be an object")
    party_defaults = {
        "floor_two_cleared": False,
        "floor_two_runs_started_after_clear": 0,
        "floor_two_run_id": None,
        "floor_two_outing_xp_multiplier_percent": 100,
        "resolved_run_events": [],
    }
    for key, value in party_defaults.items():
        if key in party:
            raise SaveStateValidationError(
                f"legacy party already contains {key}"
            )
        party[key] = value
    if "discovered_permanent_discovery_sources" in world:
        raise SaveStateValidationError(
            "legacy world already contains discovered discovery sources"
        )
    claims = world.get("permanent_discovery_claims", [])
    world["discovered_permanent_discovery_sources"] = list(claims)
    _add_floor_three_defaults(document)


def _add_floor_three_defaults(document):
    party = document.get("party")
    if not isinstance(party, dict):
        raise SaveStateValidationError("game.party must be an object")
    defaults = {
        "floor_three_cleared": False,
        "floor_three_runs_started_after_clear": 0,
        "floor_three_run_id": None,
        "floor_three_outing_xp_multiplier_percent": 100,
    }
    for key, value in defaults.items():
        if key in party:
            raise SaveStateValidationError(f"legacy party already contains {key}")
        party[key] = value


def _add_equipment_defaults(document):
    player = document.get("player")
    party = document.get("party")
    if not isinstance(player, dict) or not isinstance(party, dict):
        raise SaveStateValidationError("legacy game is missing equipment owners")
    players = [player]
    companions = party.get("companions")
    if not isinstance(companions, list):
        raise SaveStateValidationError("legacy party companions are invalid")
    players.extend(companions)
    for member in players:
        if not isinstance(member, dict):
            raise SaveStateValidationError("legacy Drifter is invalid")
        if "equipment_refs" in member:
            raise SaveStateValidationError(
                "legacy Drifter already contains M5 equipment references"
            )
        member["equipment_refs"] = {
            slot: None for slot in PlayerState.EQUIPMENT_REFERENCE_SLOTS
        }
    if "equipment_instances" in party:
        raise SaveStateValidationError(
            "legacy party already contains M5 equipment instances"
        )
    party["equipment_instances"] = []
    if "modifier_instances" in party:
        raise SaveStateValidationError(
            "legacy party already contains M5 modifier instances"
        )
    party["modifier_instances"] = []


def _add_armor_generation_defaults(document):
    party = document.get("party")
    instances = party.get("equipment_instances") if isinstance(party, dict) else None
    if not isinstance(instances, list):
        raise SaveStateValidationError(
            "legacy party equipment instances are invalid"
        )
    historical_keys = {
        "instance_id",
        "definition_id",
        "source_id",
        "secured",
        "stat_bonuses",
    }
    for index, instance in enumerate(instances):
        if not isinstance(instance, dict) or set(instance) != historical_keys:
            raise SaveStateValidationError(
                f"legacy equipment instance {index} has an invalid schema-19 shape"
            )
        try:
            template = get_equipment_template(instance.get("definition_id"))
        except (TypeError, ValueError) as error:
            raise SaveStateValidationError(
                f"legacy equipment instance {index} has an unknown definition"
            ) from error
        instance["rarity"] = "common" if template.is_armor else None
        instance["upgrade_rank"] = 0
        instance["modifier_slots"] = {}
    if "modifier_instances" in party:
        raise SaveStateValidationError(
            "schema-19 party already contains M5 modifier instances"
        )
    party["modifier_instances"] = []


def _strip_companion_combat(party):
    if not isinstance(party, dict):
        return
    companions = party.get("companions")
    if isinstance(companions, list):
        for companion in companions:
            if isinstance(companion, dict):
                companion.pop("combat", None)


def _validate_player(
    player,
    *,
    require_signature_weapon=True,
    require_advancement=False,
    require_respec_state=False,
    require_discovery_bonuses=False,
    require_equipment_refs=False,
    equipment_stat_bonuses=None,
):
    _require_mapping(player, "player")
    allowed_keys = {
        "identity",
        "attributes",
        "resources",
        "progression",
        "gold",
        "inventory",
        "run_state",
        "equipment",
    }
    if require_signature_weapon:
        allowed_keys.add("signature_weapon")
    if require_advancement:
        allowed_keys.add("advancement")
    if require_discovery_bonuses:
        allowed_keys.add("permanent_discovery_bonuses")
    if require_equipment_refs:
        allowed_keys.add("equipment_refs")
    _require_exact_keys(
        {key for key in player if key != "combat"},
        allowed_keys,
        "player",
    )
    profile = _canonical_profile(player)
    _validate_stats(player["attributes"])
    progression = player["progression"]
    _require_mapping(progression, "player.progression")
    _require_exact_keys(
        progression,
        {"level", "exp", "growth_points"},
        "player.progression",
    )
    _require_int_range(progression["level"], MINIMUM_LEVEL, MAXIMUM_LEVEL, "player.progression.level")
    threshold = xp_required_for_next_level(progression["level"])
    _require_int(progression["exp"], "player.progression.exp")
    if progression["exp"] < 0 or (threshold is not None and progression["exp"] >= threshold) or (threshold is None and progression["exp"] != 0):
        raise SaveStateValidationError("player progression contains invalid EXP")
    _require_int_min(progression["growth_points"], 0, "player.progression.growth_points")
    discovery_bonuses = (
        player.get("permanent_discovery_bonuses")
        if require_discovery_bonuses
        else {"max_hp": 0, "max_mana": 0, "growth_points_awarded": 0}
    )
    if require_discovery_bonuses:
        _validate_permanent_discovery_bonuses(discovery_bonuses)
    if require_equipment_refs:
        _validate_equipment_references(
            player["equipment_refs"], "player.equipment_refs"
        )
    if progression["growth_points"] > (
        (progression["level"] - 1) * 3
        + discovery_bonuses["growth_points_awarded"]
    ):
        raise SaveStateValidationError("player growth points exceed earned points")
    _validate_resources(
        player["resources"],
        player["attributes"],
        progression,
        discovery_bonuses,
        equipment_stat_bonuses,
    )
    _require_int_min(player["gold"], 0, "player.gold")
    if not isinstance(player["inventory"], list):
        raise SaveStateValidationError("player.inventory must be a list")
    for index, item in enumerate(player["inventory"]):
        _validate_item(item, f"player.inventory[{index}]")
    _validate_run_state(player["run_state"])
    equipment = player["equipment"]
    _require_mapping(equipment, "player.equipment")
    _require_exact_keys(equipment, set(PlayerState.EQUIPMENT_SLOTS), "player.equipment")
    for slot, item in equipment.items():
        if item is not None:
            _validate_weapon(item, f"player.equipment.{slot}")
    if require_signature_weapon:
        _validate_signature_weapon(player["signature_weapon"], equipment)
    if require_advancement:
        _validate_advancement(
            player["advancement"],
            profile,
            progression["level"],
            player["attributes"],
            progression["growth_points"],
            (progression["level"] - 1) * 3
            + discovery_bonuses["growth_points_awarded"],
            require_respec_state=require_respec_state,
        )


def _validate_permanent_discovery_bonuses(bonuses):
    _require_mapping(bonuses, "player.permanent_discovery_bonuses")
    _require_exact_keys(
        bonuses,
        {"max_hp", "max_mana", "growth_points_awarded"},
        "player.permanent_discovery_bonuses",
    )
    for name, value in bonuses.items():
        _require_int_min(value, 0, f"player.permanent_discovery_bonuses.{name}")


def _validate_advancement(
    snapshot,
    profile,
    level,
    attributes,
    growth_points,
    earned_growth_points,
    *,
    require_respec_state,
):
    try:
        normal_move_ids, super_move_ids = move_ids_for_kit(
            profile.drifter_id,
            profile.combat_moves,
        )
        advancement = AdvancementState.from_snapshot(
            profile.drifter_id,
            normal_move_ids,
            super_move_ids,
            snapshot,
            level=level,
            require_respec_state=require_respec_state,
        )
        if require_respec_state:
            for stat_name, purchased in snapshot["purchased_stat_points"].items():
                starting = getattr(profile.stats, stat_name)
                if purchased > attributes[stat_name] - starting:
                    raise ValueError(
                        f"purchased {stat_name} points exceed the Drifter's stats"
                    )
        if growth_points + advancement.purchased_growth_point_cost > earned_growth_points:
            raise ValueError("advancement purchases exceed earned Growth Points")
    except (KeyError, TypeError, ValueError) as error:
        raise SaveStateValidationError(
            f"player advancement is invalid: {error}"
        ) from error


def _validate_signature_weapon(snapshot, equipment):
    _require_mapping(snapshot, "player.signature_weapon")
    _require_exact_keys(
        snapshot,
        {
            "weapon_id",
            "components",
            "slot_progress",
            "learned_technique_ids",
            "tier_v_success",
        },
        "player.signature_weapon",
    )
    weapon_id = snapshot["weapon_id"]
    if not isinstance(weapon_id, str) or not weapon_id:
        raise SaveStateValidationError(
            "player.signature_weapon.weapon_id must be a non-empty string"
        )
    weapon_snapshot = equipment["weapon"]
    if weapon_snapshot is None:
        raise SaveStateValidationError("signature weapon is not equipped")
    try:
        weapon = create_weapon_from_persistence_key(weapon_snapshot["type"])
        progression = get_weapon_spec(weapon.item_id).progression
    except (KeyError, TypeError, ValueError) as error:
        raise SaveStateValidationError("signature weapon is invalid") from error
    if weapon_id != weapon.item_id:
        raise SaveStateValidationError(
            "signature weapon ID does not match equipped weapon"
        )
    if progression is None:
        raise SaveStateValidationError("signature weapon progression is missing")
    components = snapshot["components"]
    _require_mapping(components, "player.signature_weapon.components")
    expected_slots = {slot.slot_id for slot in progression.slots}
    _require_exact_keys(
        components,
        expected_slots,
        "player.signature_weapon.components",
    )
    for slot_id, component_id in components.items():
        if not isinstance(component_id, str) or not component_id:
            raise SaveStateValidationError(
                f"player.signature_weapon.components.{slot_id} must be a non-empty string"
            )
        try:
            component = get_weapon_component_spec(progression, component_id)
        except ValueError as error:
            raise SaveStateValidationError(
                f"player.signature_weapon.components.{slot_id} is unknown"
            ) from error
        if component.slot_id != slot_id:
            raise SaveStateValidationError(
                f"player.signature_weapon.components.{slot_id} is incompatible with its slot"
            )
    slots = snapshot["slot_progress"]
    _require_mapping(slots, "player.signature_weapon.slot_progress")
    _require_exact_keys(
        slots,
        expected_slots,
        "player.signature_weapon.slot_progress",
    )
    for slot_id, value in slots.items():
        _require_int_range(
            value,
            0,
            100,
            f"player.signature_weapon.slot_progress.{slot_id}",
        )
    techniques = snapshot["learned_technique_ids"]
    if not isinstance(techniques, list):
        raise SaveStateValidationError(
            "player.signature_weapon.learned_technique_ids must be a list"
        )
    if any(not isinstance(technique_id, str) or not technique_id for technique_id in techniques):
        raise SaveStateValidationError("learned technique IDs must be non-empty strings")
    if len(techniques) != len(set(techniques)):
        raise SaveStateValidationError("learned technique IDs must be unique")
    if not isinstance(snapshot["tier_v_success"], bool):
        raise SaveStateValidationError(
            "player.signature_weapon.tier_v_success must be a boolean"
        )


def _validate_stats(attributes):
    _require_mapping(attributes, "player.attributes")
    _require_exact_keys(attributes, set(PermanentStats.STAT_NAMES), "player.attributes")
    for name in PermanentStats.STAT_NAMES:
        _require_int_range(attributes[name], 1, 100, f"player.attributes.{name}")


def _validate_resources(
    resources,
    attributes,
    progression,
    discovery_bonuses=None,
    equipment_stat_bonuses=None,
):
    _require_mapping(resources, "player.resources")
    _require_exact_keys(resources, {"health", "mana", "super"}, "player.resources")
    level = progression["level"]
    bonuses = discovery_bonuses or {"max_hp": 0, "max_mana": 0}
    equipment_bonuses = equipment_stat_bonuses or {}
    expected_health = (
        _maximum_hp(
            attributes["constitution"] + equipment_bonuses.get("constitution", 0),
            level,
        )
        + bonuses["max_hp"]
    )
    expected_mana = (
        _maximum_mana(
            attributes["spirit"] + equipment_bonuses.get("spirit", 0),
            level,
        )
        + bonuses["max_mana"]
    )
    for name, expected_maximum in (("health", expected_health), ("mana", expected_mana)):
        resource = resources[name]
        _require_mapping(resource, f"player.resources.{name}")
        _require_exact_keys(resource, {"current", "maximum"}, f"player.resources.{name}")
        if resource["maximum"] != expected_maximum:
            raise SaveStateValidationError(f"{name} maximum does not match canonical scaling")
        _require_int_range(resource["current"], 0, expected_maximum, f"player.resources.{name}.current")
    super_resource = resources["super"]
    _require_mapping(super_resource, "player.resources.super")
    _require_exact_keys(super_resource, {"current", "maximum"}, "player.resources.super")
    if super_resource["maximum"] != Super.MAXIMUM:
        raise SaveStateValidationError("super maximum is not canonical")
    _require_int_range(super_resource["current"], 0, Super.MAXIMUM, "player.resources.super.current")


def _maximum_hp(constitution, level):
    from app.player.scaling import maximum_hp_from_constitution
    return maximum_hp_from_constitution(constitution, level=level)


def _maximum_mana(spirit, level):
    from app.player.scaling import maximum_mana_from_spirit
    return maximum_mana_from_spirit(spirit, level=level)


def _validate_item(item, path):
    if isinstance(item, dict):
        _validate_weapon(item, path)
    elif not (item is None or isinstance(item, (str, bool, int, float))):
        raise SaveStateValidationError(f"{path} is not a serializable item")


def _validate_weapon(item, path):
    _require_mapping(item, path)
    _reconstruct_weapon(item, path)


def _validate_run_state(run_state):
    _require_mapping(run_state, "player.run_state")
    _require_exact_keys(run_state, {"inventory", "prepared_payloads"}, "player.run_state")
    inventory = run_state["inventory"]
    _require_mapping(inventory, "player.run_state.inventory")
    for item_id, quantity in inventory.items():
        try:
            RunItemId(item_id)
        except (TypeError, ValueError) as error:
            raise SaveStateValidationError("unknown run item identifier") from error
        _require_int_min(quantity, 0, f"player.run_state.inventory.{item_id}")
    payloads = run_state["prepared_payloads"]
    _require_mapping(payloads, "player.run_state.prepared_payloads")
    for payload_id, infusion in payloads.items():
        try:
            PreparedPayloadId(payload_id)
        except (TypeError, ValueError) as error:
            raise SaveStateValidationError("unknown prepared payload identifier") from error
        if infusion is not None:
            try:
                InfusionKind(infusion)
            except (TypeError, ValueError) as error:
                raise SaveStateValidationError("unknown infusion kind") from error


def _validate_story(story):
    _require_mapping(story, "story")
    _require_exact_keys(story, {"current_chapter", "current_scene", "current_location", "story_flags", "completed_events", "player_decisions"}, "story")
    for name in ("current_chapter", "current_scene", "current_location"):
        if story[name] is not None and not isinstance(story[name], str):
            raise SaveStateValidationError(f"story.{name} must be a string or null")
    _validate_unique_string_list(story["story_flags"], "story.story_flags")
    _validate_unique_string_list(story["completed_events"], "story.completed_events")
    _require_mapping(story["player_decisions"], "story.player_decisions")
    validate_plain_value(story["player_decisions"], "story.player_decisions")


def _validate_world(
    world,
    *,
    require_permanent_discovery_claims=False,
    require_discovered_permanent_discovery_sources=False,
    require_authored_discovery_sources=False,
):
    _require_mapping(world, "world")
    expected_keys = {
        "discovered_locations",
        "defeated_encounters",
        "opened_objects",
        "consumed_objects",
        "dungeon_changes",
    }
    if require_permanent_discovery_claims:
        expected_keys.add("permanent_discovery_claims")
    if require_discovered_permanent_discovery_sources:
        expected_keys.add("discovered_permanent_discovery_sources")
    _require_exact_keys(world, expected_keys, "world")
    for name in ("discovered_locations", "defeated_encounters", "opened_objects", "consumed_objects"):
        _validate_unique_string_list(world[name], f"world.{name}")
    if require_permanent_discovery_claims:
        _validate_unique_string_list(
            world["permanent_discovery_claims"],
            "world.permanent_discovery_claims",
        )
        if any(
            not is_valid_permanent_discovery_source_id(value)
            for value in world["permanent_discovery_claims"]
        ):
            raise SaveStateValidationError(
                "world contains a malformed permanent discovery source ID"
            )
        if require_authored_discovery_sources:
            _validate_authored_discovery_source_ids(
                world["permanent_discovery_claims"]
            )
    if require_discovered_permanent_discovery_sources:
        _validate_unique_string_list(
            world["discovered_permanent_discovery_sources"],
            "world.discovered_permanent_discovery_sources",
        )
        discovered_sources = world["discovered_permanent_discovery_sources"]
        if any(
            not is_valid_permanent_discovery_source_id(value)
            for value in discovered_sources
        ):
            raise SaveStateValidationError(
                "world contains a malformed discovered discovery source ID"
            )
        if require_authored_discovery_sources:
            _validate_authored_discovery_source_ids(discovered_sources)
        if not set(world["permanent_discovery_claims"]).issubset(
            discovered_sources
        ):
            raise SaveStateValidationError(
                "claimed discovery sources must be recorded as discovered"
            )
    _require_mapping(world["dungeon_changes"], "world.dungeon_changes")
    validate_plain_value(world["dungeon_changes"], "world.dungeon_changes")


def _validate_authored_discovery_source_ids(source_ids):
    for source_id in source_ids:
        try:
            get_known_permanent_discovery_source(source_id)
        except ValueError as error:
            raise SaveStateValidationError(
                f"world contains an unknown permanent discovery source: {source_id}"
            ) from error


def _validate_discovery_event_world_relationship(world, party):
    discovered = set(world["discovered_permanent_discovery_sources"])
    found = {
        event["result"]["source_id"]
        for event in party["resolved_run_events"]
        if event["kind"] == "discovery_search" and event["result"]["found"]
    }
    if not found.issubset(discovered):
        raise SaveStateValidationError(
            "successful discovery events must be recorded as discovered sources"
        )


def _validate_legacy_overworld(overworld, world):
    _require_mapping(overworld, "overworld")
    _require_exact_keys(overworld, {"current_route_node_id", "surface_route_begun", "dungeon_entrance_reached", "route_complete", "resolved_rest_node_ids", "current_contextual_route_phase"}, "overworld")
    node_id = overworld["current_route_node_id"]
    try:
        node = get_route_node_spec(node_id)
    except (TypeError, ValueError) as error:
        raise SaveStateValidationError("overworld has an unknown route node") from error
    for name in ("surface_route_begun", "dungeon_entrance_reached", "route_complete"):
        if not isinstance(overworld[name], bool):
            raise SaveStateValidationError(f"overworld.{name} must be a boolean")
    index = _SURFACE_ROUTE_NODE_IDS.index(node_id)
    if index > 0 and not overworld["surface_route_begun"]:
        raise SaveStateValidationError("advanced route must have begun")
    at_dungeon = node_id == _DUNGEON_ENTRANCE_NODE_ID
    if overworld["dungeon_entrance_reached"] != at_dungeon or overworld["route_complete"] != at_dungeon:
        raise SaveStateValidationError("overworld completion flags are inconsistent")
    rests = overworld["resolved_rest_node_ids"]
    required_rests = [
        route_node_id
        for route_node_id in _SURFACE_ROUTE_NODE_IDS[:index]
        if get_route_node_spec(route_node_id).kind is RouteNodeKind.REST
    ]
    if rests != required_rests:
        raise SaveStateValidationError("resolved Rest IDs must use authored order")
    if not isinstance(rests, list) or any(
        rest not in _SURFACE_REST_NODE_IDS for rest in rests
    ):
        raise SaveStateValidationError("overworld contains an unknown Rest ID")
    phase = overworld["current_contextual_route_phase"]
    try:
        phase = ContextualRoutePhase(phase)
    except (TypeError, ValueError) as error:
        raise SaveStateValidationError("overworld has an invalid contextual phase") from error
    if node.kind in {RouteNodeKind.REST, RouteNodeKind.DUNGEON_ENTRANCE} and phase is not ContextualRoutePhase.NONE:
        raise SaveStateValidationError("Rest and dungeon nodes cannot offer combat phases")
    if node.kind in {RouteNodeKind.COMBAT, RouteNodeKind.BOSS} and phase not in {
        ContextualRoutePhase.ENTER_ENCOUNTER,
        ContextualRoutePhase.RETRY,
    }:
        raise SaveStateValidationError("combat nodes require an encounter phase")
    route_encounters = set(_SURFACE_ENCOUNTER_NODES)
    required_encounters = {
        node.encounter_id
        for node in _SURFACE_ROUTE.nodes[:index]
        if node.encounter_id is not None
    }
    route_defeated = {
        encounter_id
        for encounter_id in world["defeated_encounters"]
        if encounter_id in route_encounters
    }
    if route_defeated != required_encounters:
        raise SaveStateValidationError("route completion is not a valid authored prefix")
    for encounter_id in world["defeated_encounters"]:
        if encounter_id in route_encounters:
            encounter_node = _SURFACE_ENCOUNTER_NODES[encounter_id]
            route_index = _SURFACE_ROUTE_NODE_IDS.index(encounter_node.node_id)
            if encounter_node.kind not in {
                RouteNodeKind.COMBAT,
                RouteNodeKind.BOSS,
            }:
                raise SaveStateValidationError("non-combat route node is not an encounter")
            if route_index >= index:
                raise SaveStateValidationError("a future route encounter is already defeated")


def _validate_overworld(overworld, world, *, allow_floor_three=False):
    _require_mapping(overworld, "overworld")
    _require_exact_keys(
        overworld,
        {
            "active_route_id",
            "current_route_node_id",
            "surface_route_begun",
            "dungeon_entrance_reached",
            "route_complete",
            "resolved_rest_node_ids",
            "current_contextual_route_phase",
        },
        "overworld",
    )
    route_id = overworld["active_route_id"]
    if route_id == "surface":
        _validate_legacy_overworld(
            {
                key: value
                for key, value in overworld.items()
                if key != "active_route_id"
            },
            world,
        )
        return
    if route_id == "floor_three" and not allow_floor_three:
        raise SaveStateValidationError(
            "legacy save cannot contain an active Floor 3 route"
        )
    if route_id not in {"floor_one", "floor_two", "floor_three"}:
        raise SaveStateValidationError("overworld has an unknown active route")
    route = {
        "floor_one": _FLOOR_ONE_ROUTE,
        "floor_two": _FLOOR_TWO_ROUTE,
        "floor_three": _FLOOR_THREE_ROUTE,
    }[route_id]
    route_node_ids = {
        "floor_one": _FLOOR_ONE_ROUTE_NODE_IDS,
        "floor_two": _FLOOR_TWO_ROUTE_NODE_IDS,
        "floor_three": _FLOOR_THREE_ROUTE_NODE_IDS,
    }[route_id]
    floor_label = {
        "floor_one": "Floor 1",
        "floor_two": "Floor 2",
        "floor_three": "Floor 3",
    }[route_id]
    node_id = overworld["current_route_node_id"]
    if node_id not in route_node_ids:
        raise SaveStateValidationError(
            f"{floor_label} cursor does not belong to the active route"
        )
    for name in ("surface_route_begun", "dungeon_entrance_reached", "route_complete"):
        if not isinstance(overworld[name], bool):
            raise SaveStateValidationError(f"overworld.{name} must be a boolean")
    if (
        not overworld["surface_route_begun"]
        or not overworld["dungeon_entrance_reached"]
        or overworld["route_complete"]
    ):
        raise SaveStateValidationError(
            f"{floor_label} requires a completed Surface entrance and active route"
        )

    route_index = route_node_ids.index(node_id)
    node = get_route_node_spec(node_id)
    rests = overworld["resolved_rest_node_ids"]
    required_rests = [
        route_node.node_id
        for route_node in route.nodes[:route_index]
        if route_node.kind is RouteNodeKind.REST
    ]
    if not isinstance(rests, list) or rests != required_rests:
        raise SaveStateValidationError(
            f"{floor_label} resolved Rest IDs must match the authored route prefix"
        )
    phase = overworld["current_contextual_route_phase"]
    try:
        phase = ContextualRoutePhase(phase)
    except (TypeError, ValueError) as error:
        raise SaveStateValidationError(
            "overworld has an invalid contextual phase"
        ) from error
    if node.kind is RouteNodeKind.REST and phase is not ContextualRoutePhase.NONE:
        raise SaveStateValidationError("Rest nodes cannot offer combat phases")
    if node.kind in {RouteNodeKind.COMBAT, RouteNodeKind.BOSS} and phase not in {
        ContextualRoutePhase.ENTER_ENCOUNTER,
        ContextualRoutePhase.RETRY,
    }:
        raise SaveStateValidationError("combat nodes require an encounter phase")
    if node.kind not in {
        RouteNodeKind.REST,
        RouteNodeKind.COMBAT,
        RouteNodeKind.BOSS,
    }:
        raise SaveStateValidationError(
            f"{floor_label} contains an unsupported route node"
        )

    surface_progress = {
        "current_route_node_id": _DUNGEON_ENTRANCE_NODE_ID,
        "surface_route_begun": True,
        "dungeon_entrance_reached": True,
        "route_complete": True,
        "resolved_rest_node_ids": list(_SURFACE_REST_NODE_IDS),
        "current_contextual_route_phase": ContextualRoutePhase.NONE.value,
    }
    _validate_legacy_overworld(surface_progress, world)


def _validate_route_party_relationship(
    overworld,
    party,
    *,
    require_floor_three_state=False,
):
    route_id = overworld["active_route_id"]
    phase = DungeonPhase(party["phase"])
    if route_id == "surface":
        at_entrance = (
            overworld["current_route_node_id"] == _DUNGEON_ENTRANCE_NODE_ID
        )
        if at_entrance != (phase is not DungeonPhase.OUTSIDE):
            raise SaveStateValidationError(
                "dungeon entrance and party phase are inconsistent"
            )
        if phase is DungeonPhase.OUTING:
            raise SaveStateValidationError(
                "outing cannot be saved without a battle snapshot"
            )
        return

    if route_id == "floor_two":
        if (
            phase is not DungeonPhase.OUTING
            or not party["tutorial_complete"]
            or not party["companions"]
            or not party["floor_one_cleared"]
            or party["floor_two_run_id"] is None
        ):
            raise SaveStateValidationError(
                "Floor 2 requires an unlocked active outing with the recruited party"
            )
        return

    if route_id == "floor_three":
        if not require_floor_three_state:
            raise SaveStateValidationError(
                "legacy save cannot contain an active Floor 3 route"
            )
        if (
            phase is not DungeonPhase.OUTING
            or not party["tutorial_complete"]
            or len(party["companions"]) != 3
            or not party["floor_two_cleared"]
            or party["floor_three_run_id"] is None
        ):
            raise SaveStateValidationError(
                "Floor 3 requires an unlocked active outing with four recruited Drifters"
            )
        return

    if (
        phase is not DungeonPhase.OUTING
        or not party["tutorial_complete"]
        or not party["companions"]
    ):
        raise SaveStateValidationError(
            "Floor 1 requires an active outing with the recruited party"
        )
    current_node = get_route_node_spec(overworld["current_route_node_id"])
    if current_node.kind is not RouteNodeKind.REST:
        raise SaveStateValidationError(
            "only a Floor 1 Rest can be saved during an outing"
        )
    if current_node.node_id in overworld["resolved_rest_node_ids"]:
        raise SaveStateValidationError(
            "only an unresolved Floor 1 Rest can be saved"
        )


def _opening_overworld_snapshot():
    return {
        "active_route_id": "surface",
        "current_route_node_id": _FIRST_SURFACE_NODE_ID,
        "surface_route_begun": False,
        "dungeon_entrance_reached": False,
        "route_complete": False,
        "resolved_rest_node_ids": [],
        "current_contextual_route_phase": ContextualRoutePhase.ENTER_ENCOUNTER.value,
    }


def _empty_story_snapshot():
    return {
        "current_chapter": None,
        "current_scene": None,
        "current_location": None,
        "story_flags": [],
        "completed_events": [],
        "player_decisions": {},
    }


def _empty_world_snapshot():
    return {
        "discovered_locations": [],
        "defeated_encounters": [],
        "opened_objects": [],
        "consumed_objects": [],
        "dungeon_changes": {},
    }


def _validate_plain_document(document):
    try:
        validate_plain_value(document, "save")
    except (TypeError, ValueError) as error:
        raise SaveStateValidationError(str(error)) from error
    _require_mapping(document, "save")


def _require_mapping(value, path):
    if not isinstance(value, dict):
        raise SaveStateValidationError(f"{path} must be an object")


def _require_exact_keys(value, expected, path):
    if set(value) != expected:
        raise SaveStateValidationError(f"{path} has an invalid shape")


def _require_int(value, path):
    if isinstance(value, bool) or not isinstance(value, int):
        raise SaveStateValidationError(f"{path} must be an integer")


def _require_int_min(value, minimum, path):
    _require_int(value, path)
    if value < minimum:
        raise SaveStateValidationError(f"{path} is below its minimum")


def _require_int_range(value, minimum, maximum, path):
    _require_int(value, path)
    if value < minimum or value > maximum:
        raise SaveStateValidationError(f"{path} is outside its allowed range")


def _validate_unique_string_list(value, path):
    if not isinstance(value, list):
        raise SaveStateValidationError(f"{path} must be a list")
    if any(not isinstance(item, str) for item in value):
        raise SaveStateValidationError(f"{path} must contain strings")
    if len(value) != len(set(value)):
        raise SaveStateValidationError(f"{path} must not contain duplicates")


__all__ = [
    "DISK_SCHEMA_VERSION",
    "SaveStateValidationError",
    "build_save_document",
    "migrate_schema_7",
    "migrate_schema_9",
    "migrate_schema_12",
    "migrate_schema_13",
    "migrate_schema15",
    "migrate_schema16",
    "reconstruct_game_state",
    "validate_legacy_schema8_document",
    "validate_legacy_schema9_document",
    "validate_legacy_schema12_document",
    "validate_legacy_schema13_document",
    "validate_legacy_schema15_document",
    "validate_legacy_schema16_document",
    "validate_profile_payload",
    "validate_save_document",
]

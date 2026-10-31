"""Schema-14 save documents and canonical in-memory reconstruction."""

from copy import deepcopy

from app.content.catalog import (
    create_weapon_from_persistence_key,
    get_drifter_spec_by_choice,
    get_route_node_spec,
    get_route_spec,
    get_weapon_spec,
)
from app.content.hub_economy import get_supply_item
from app.content.route_spec import RouteNodeKind
from app.content.weapon_progression_spec import (
    MAX_CRAFTING_EXPERIENCE,
    get_weapon_component_spec,
)
from app.game.game_state import GameState
from app.game.overworld_state import ContextualRoutePhase, OverworldState
from app.game.party_state import DungeonPhase, PartyState
from app.game.story_state import StoryState
from app.game.world_state import WorldState
from app.player.character_run_state import (
    CharacterRunCheckpoint,
    InfusionKind,
    PreparedPayloadId,
    RunItemId,
)
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


_LEGACY_RUNTIME_SCHEMA_VERSION = 7
_LEGACY_DISK_SCHEMA_VERSION = 8
_PREVIOUS_DISK_SCHEMA_VERSION = 9
_PREVIOUS_CURRENT_DISK_SCHEMA_VERSION = 10
_CURRENT_PREVIOUS_DISK_SCHEMA_VERSION = 11
_PREVIOUS_DISK_SCHEMA_VERSION_CURRENT = 12
_LATEST_PREVIOUS_DISK_SCHEMA_VERSION = 13
DISK_SCHEMA_VERSION = 14


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
    _validate_document(source, schema_version=DISK_SCHEMA_VERSION)
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
    _validate_document(migrated, schema_version=DISK_SCHEMA_VERSION)
    return migrated


def migrate_schema_12(document):
    """Upgrade an immutable schema-12 payload with its legacy deployed pair."""
    validate_legacy_schema12_document(document)
    migrated = deepcopy(document)
    migrated["schema_version"] = DISK_SCHEMA_VERSION
    _add_legacy_active_drifter_ids(migrated)
    _add_carried_supply_defaults(migrated)
    _validate_document(migrated, schema_version=DISK_SCHEMA_VERSION)
    return migrated


def migrate_schema_13(document):
    """Upgrade a schema-13 save with an empty carried-supplies pack."""
    validate_legacy_schema13_document(document)
    migrated = deepcopy(document)
    migrated["schema_version"] = DISK_SCHEMA_VERSION
    _add_carried_supply_defaults(migrated)
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


def validate_legacy_schema8_document(document):
    """Validate and copy an original schema-8 disk payload without migrating it."""
    _validate_plain_document(document)
    _validate_legacy_schema8_document(document)
    return deepcopy(document)


def validate_profile_payload(document):
    """Validate a current payload or immutable schema-8 through schema-13 history."""
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
        and document.get("schema_version") == _PREVIOUS_CURRENT_DISK_SCHEMA_VERSION
    ):
        return validate_legacy_schema10_document(document)
    normalized = validate_save_document(document)
    if normalized != document:
        raise SaveStateValidationError("profile payload is not canonical")
    return normalized


def reconstruct_game_state(document):
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
        party = PartyState.from_snapshot(document["party"], companions=companions)
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
    if schema_version == DISK_SCHEMA_VERSION:
        normalized = deepcopy(document)
        if isinstance(normalized.get("player"), dict):
            normalized["player"].pop("combat", None)
        _strip_companion_combat(normalized.get("party"))
        _validate_document(normalized, schema_version=DISK_SCHEMA_VERSION)
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
    _validate_player(
        document["player"],
        require_signature_weapon=require_signature_weapon,
    )
    _validate_story(document["story"])
    _validate_world(document["world"])
    _validate_overworld(
        document["overworld"],
        document["world"],
    )
    _validate_party(
        document["party"],
        document["player"],
        require_signature_weapon=require_signature_weapon,
        require_active_drifter_ids=(
            schema_version >= _LATEST_PREVIOUS_DISK_SCHEMA_VERSION
        ),
        require_carried_supplies=schema_version == DISK_SCHEMA_VERSION,
    )
    _validate_route_party_relationship(document["overworld"], document["party"])
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
    require_active_drifter_ids=False,
    require_carried_supplies=False,
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
    _require_exact_keys(party, expected_keys, "party")
    companions = party["companions"]
    max_companions = 3 if require_active_drifter_ids else 1
    if not isinstance(companions, list) or len(companions) > max_companions:
        raise SaveStateValidationError(
            f"party.companions must contain at most {max_companions} Drifters"
        )
    lead_profile = _canonical_profile(player)
    companion_ids = set()
    for companion in companions:
        _validate_player(
            companion,
            require_signature_weapon=require_signature_weapon,
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


def _validate_item_stacks(items, path):
    _require_mapping(items, path)
    for item_id, quantity in items.items():
        if not isinstance(item_id, str) or not item_id:
            raise SaveStateValidationError(f"{path} contains an invalid item ID")
        _require_int_min(quantity, 1, f"{path}.{item_id}")


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


def _strip_companion_combat(party):
    if not isinstance(party, dict):
        return
    companions = party.get("companions")
    if isinstance(companions, list):
        for companion in companions:
            if isinstance(companion, dict):
                companion.pop("combat", None)


def _validate_player(player, *, require_signature_weapon=True):
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
    _require_exact_keys(
        {key for key in player if key != "combat"},
        allowed_keys,
        "player",
    )
    _canonical_profile(player)
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
    if progression["growth_points"] > (progression["level"] - 1) * 3:
        raise SaveStateValidationError("player growth points exceed earned points")
    _validate_resources(player["resources"], player["attributes"], progression)
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


def _validate_resources(resources, attributes, progression):
    _require_mapping(resources, "player.resources")
    _require_exact_keys(resources, {"health", "mana", "super"}, "player.resources")
    level = progression["level"]
    expected_health = _maximum_hp(attributes["constitution"], level)
    expected_mana = _maximum_mana(attributes["spirit"], level)
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


def _validate_world(world):
    _require_mapping(world, "world")
    _require_exact_keys(world, {"discovered_locations", "defeated_encounters", "opened_objects", "consumed_objects", "dungeon_changes"}, "world")
    for name in ("discovered_locations", "defeated_encounters", "opened_objects", "consumed_objects"):
        _validate_unique_string_list(world[name], f"world.{name}")
    _require_mapping(world["dungeon_changes"], "world.dungeon_changes")
    validate_plain_value(world["dungeon_changes"], "world.dungeon_changes")


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


def _validate_overworld(overworld, world):
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
    if route_id != "floor_one":
        raise SaveStateValidationError("overworld has an unknown active route")

    node_id = overworld["current_route_node_id"]
    if node_id not in _FLOOR_ONE_ROUTE_NODE_IDS:
        raise SaveStateValidationError(
            "Floor 1 cursor does not belong to the active route"
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
            "Floor 1 requires a completed Surface entrance and active route"
        )

    route_index = _FLOOR_ONE_ROUTE_NODE_IDS.index(node_id)
    node = get_route_node_spec(node_id)
    rests = overworld["resolved_rest_node_ids"]
    required_rests = [
        route_node.node_id
        for route_node in _FLOOR_ONE_ROUTE.nodes[:route_index]
        if route_node.kind is RouteNodeKind.REST
    ]
    if not isinstance(rests, list) or rests != required_rests:
        raise SaveStateValidationError(
            "Floor 1 resolved Rest IDs must match the authored route prefix"
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
        raise SaveStateValidationError("Floor 1 contains an unsupported route node")

    surface_progress = {
        "current_route_node_id": _DUNGEON_ENTRANCE_NODE_ID,
        "surface_route_begun": True,
        "dungeon_entrance_reached": True,
        "route_complete": True,
        "resolved_rest_node_ids": list(_SURFACE_REST_NODE_IDS),
        "current_contextual_route_phase": ContextualRoutePhase.NONE.value,
    }
    _validate_legacy_overworld(surface_progress, world)


def _validate_route_party_relationship(overworld, party):
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
    "reconstruct_game_state",
    "validate_legacy_schema8_document",
    "validate_legacy_schema9_document",
    "validate_legacy_schema12_document",
    "validate_legacy_schema13_document",
    "validate_profile_payload",
    "validate_save_document",
]

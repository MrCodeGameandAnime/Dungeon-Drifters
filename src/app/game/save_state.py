"""Schema-8 save documents and canonical in-memory reconstruction."""

from copy import deepcopy

from app.game.game_state import GameState
from app.game.overworld_route import (
    DUNGEON_ENTRANCE_NODE_ID,
    FIRST_SURFACE_NODE_ID,
    RouteNodeKind,
    SURFACE_REST_NODE_IDS,
    SURFACE_ROUTE_NODE_IDS,
    route_node,
)
from app.game.overworld_state import ContextualRoutePhase, OverworldState
from app.game.story_state import StoryState
from app.game.world_state import WorldState
from app.items.weapon import (
    NeedleOfPlainIron,
    Sathren,
    SkyNeedle,
    SunderSpire,
)
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
from app.world.character_profiles.roster import get_profile_by_choice


DISK_SCHEMA_VERSION = 8


class SaveStateValidationError(ValueError):
    """Raised when a disk save cannot be trusted or reconstructed."""


_WEAPON_TYPES = {
    cls.__name__: cls
    for cls in (SunderSpire, SkyNeedle, Sathren, NeedleOfPlainIron)
}


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
    source["schema_version"] = DISK_SCHEMA_VERSION
    _validate_document(source, schema_version=DISK_SCHEMA_VERSION)
    return source


def migrate_schema_7(document):
    _validate_plain_document(document)
    schema_version = document.get("schema_version")
    if schema_version != STATE_SCHEMA_VERSION:
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
            if encounter_id not in SURFACE_ROUTE_NODE_IDS
        ]
    _validate_document(migrated, schema_version=DISK_SCHEMA_VERSION)
    return migrated


def reconstruct_game_state(document):
    _validate_plain_document(document)
    schema_version = document.get("schema_version")
    if schema_version == STATE_SCHEMA_VERSION:
        document = migrate_schema_7(document)
    elif schema_version == DISK_SCHEMA_VERSION:
        document = deepcopy(document)
        if isinstance(document.get("player"), dict):
            document["player"].pop("combat", None)
        _validate_document(document, schema_version=DISK_SCHEMA_VERSION)
    else:
        raise SaveStateValidationError(
            f"unsupported save schema: {schema_version!r}"
        )

    try:
        profile = _canonical_profile(document["player"])
        character = profile.create_character()
        player = _reconstruct_player(character, document["player"])
        story = StoryState.from_snapshot(document["story"])
        world = WorldState.from_snapshot(document["world"])
        overworld = OverworldState.from_snapshot(document["overworld"])
        return GameState.from_persistent_parts(
            player,
            story,
            world,
            overworld,
            document["metadata"],
        )
    except (KeyError, TypeError, ValueError) as error:
        if isinstance(error, SaveStateValidationError):
            raise
        raise SaveStateValidationError(
            f"save reconstruction failed: {error}"
        ) from error


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
    profile = get_profile_by_choice(profile_data["choice"])
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
    weapon_class = _WEAPON_TYPES.get(weapon_type)
    if weapon_class is None:
        raise SaveStateValidationError(f"{path} contains an unknown weapon type")
    weapon = weapon_class()
    if payload != _weapon_payload(weapon):
        raise SaveStateValidationError(f"{path} does not match authored weapon data")
    return weapon


def _weapon_payload(weapon):
    return {
        "type": weapon.__class__.__name__,
        "name": weapon.name,
        "weapon_type": weapon.weapon_type,
        "intended_wielder": weapon.intended_wielder,
        "stat_bonuses": weapon.stat_bonuses,
        "value": weapon.value,
        "description": weapon.description,
    }


def _validate_document(document, *, schema_version):
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
    if document["schema_version"] != schema_version:
        raise SaveStateValidationError("save schema version mismatch")
    _validate_player(document["player"])
    _validate_story(document["story"])
    _validate_world(document["world"])
    _validate_overworld(document["overworld"], document["world"])
    validate_plain_value(document["metadata"], "game.metadata")


def _validate_player(player):
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


def _validate_overworld(overworld, world):
    _require_mapping(overworld, "overworld")
    _require_exact_keys(overworld, {"current_route_node_id", "surface_route_begun", "dungeon_entrance_reached", "route_complete", "resolved_rest_node_ids", "current_contextual_route_phase"}, "overworld")
    node_id = overworld["current_route_node_id"]
    try:
        node = route_node(node_id)
    except (TypeError, ValueError) as error:
        raise SaveStateValidationError("overworld has an unknown route node") from error
    for name in ("surface_route_begun", "dungeon_entrance_reached", "route_complete"):
        if not isinstance(overworld[name], bool):
            raise SaveStateValidationError(f"overworld.{name} must be a boolean")
    index = SURFACE_ROUTE_NODE_IDS.index(node_id)
    if index > 0 and not overworld["surface_route_begun"]:
        raise SaveStateValidationError("advanced route must have begun")
    at_dungeon = node_id == DUNGEON_ENTRANCE_NODE_ID
    if overworld["dungeon_entrance_reached"] != at_dungeon or overworld["route_complete"] != at_dungeon:
        raise SaveStateValidationError("overworld completion flags are inconsistent")
    rests = overworld["resolved_rest_node_ids"]
    required_rests = [
        route_node_id
        for route_node_id in SURFACE_ROUTE_NODE_IDS[:index]
        if route_node(route_node_id).kind is RouteNodeKind.REST
    ]
    if rests != required_rests:
        raise SaveStateValidationError("resolved Rest IDs must use authored order")
    if not isinstance(rests, list) or any(rest not in SURFACE_REST_NODE_IDS for rest in rests):
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
    route_encounters = set(SURFACE_ROUTE_NODE_IDS)
    required_encounters = {
        route_node_id
        for route_node_id in SURFACE_ROUTE_NODE_IDS[:index]
        if route_node(route_node_id).kind in {
            RouteNodeKind.COMBAT,
            RouteNodeKind.BOSS,
        }
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
            route_index = SURFACE_ROUTE_NODE_IDS.index(encounter_id)
            if route_node(encounter_id).kind is not RouteNodeKind.COMBAT and route_node(encounter_id).kind is not RouteNodeKind.BOSS:
                raise SaveStateValidationError("non-combat route node is not an encounter")
            if route_index >= index:
                raise SaveStateValidationError("a future route encounter is already defeated")


def _opening_overworld_snapshot():
    return {
        "current_route_node_id": FIRST_SURFACE_NODE_ID,
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
    "reconstruct_game_state",
]

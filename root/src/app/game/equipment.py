"""Authoritative per-Drifter equipment actions."""

from dataclasses import dataclass
from enum import StrEnum

from app.content.catalog import get_route_node_spec
from app.content.route_spec import RouteNodeKind
from app.game.game_state import GameState
from app.game.party_state import DungeonPhase
from app.persistence.save_port_contract import (
    SaveLoadStatus,
    SavePortError,
    is_save_port,
)


class EquipmentActionStatus(StrEnum):
    EQUIPPED = "equipped"
    INVALID_TARGET = "invalid_target"
    INVALID_INSTANCE = "invalid_instance"
    WRONG_SLOT = "wrong_slot"
    NOT_AVAILABLE = "not_available"
    SAVE_FAILED = "save_failed"


@dataclass(frozen=True)
class EquipmentActionResult:
    status: EquipmentActionStatus
    game_state: GameState


def equipment_target_members(game_state):
    if _is_unresolved_safe_rest(game_state):
        return game_state.recruited_members
    return game_state.members_available_to_party


def can_manage_equipment_target(game_state, target_drifter_id):
    try:
        game_state.member_for_drifter_id(target_drifter_id)
    except (TypeError, ValueError):
        return False
    party = game_state.party_state
    if party.phase in {DungeonPhase.HUB, DungeonPhase.PARTY_READY}:
        return True
    if party.phase not in {DungeonPhase.OUTING, DungeonPhase.EXTRACTION}:
        return False
    if _is_unresolved_safe_rest(game_state):
        return True
    if game_state.overworld_state.active_route_id != "floor_two":
        return False
    return target_drifter_id in party.active_drifter_ids


def _is_unresolved_safe_rest(game_state):
    party = game_state.party_state
    if party.phase is not DungeonPhase.OUTING:
        return False
    node_id = game_state.overworld_state.current_route_node_id
    try:
        current_node = get_route_node_spec(node_id)
    except (TypeError, ValueError):
        return False
    return (
        current_node.kind is RouteNodeKind.REST
        and node_id not in game_state.overworld_state.resolved_rest_node_ids
    )


class EquipmentService:
    def __init__(self, *, save_port):
        if not is_save_port(save_port):
            raise TypeError("save_port must satisfy SavePort")
        self._save_port = save_port

    def equip(self, game_state, *, target_drifter_id, instance_id):
        if not isinstance(game_state, GameState):
            raise TypeError("game_state must be a GameState")
        try:
            game_state.member_for_drifter_id(target_drifter_id)
        except ValueError:
            return EquipmentActionResult(
                EquipmentActionStatus.INVALID_TARGET,
                game_state,
            )
        if not self._target_can_manage(game_state, target_drifter_id):
            return EquipmentActionResult(
                EquipmentActionStatus.NOT_AVAILABLE,
                game_state,
            )
        try:
            instance = game_state.party_state.equipment_instance(instance_id)
        except ValueError:
            return EquipmentActionResult(
                EquipmentActionStatus.INVALID_INSTANCE,
                game_state,
            )
        if instance.slot_id not in game_state.member_for_drifter_id(
            target_drifter_id
        ).equipped_equipment_ids:
            return EquipmentActionResult(
                EquipmentActionStatus.WRONG_SLOT,
                game_state,
            )

        candidate = game_state.clone()
        player = candidate.member_for_drifter_id(target_drifter_id)
        for member in candidate.recruited_members:
            member_refs = member.equipped_equipment_ids
            if member_refs.get(instance.slot_id) == instance.instance_id:
                member_refs[instance.slot_id] = None
                member._set_equipped_equipment_ids(member_refs)
        refs = player.equipped_equipment_ids
        refs[instance.slot_id] = instance.instance_id
        player._set_equipped_equipment_ids(refs)
        candidate._bind_equipment_state()
        try:
            result = self._save_port.save(candidate)
        except (OSError, SavePortError, TypeError, ValueError):
            result = None
        if result is None or result.status is not SaveLoadStatus.SAVED:
            return EquipmentActionResult(
                EquipmentActionStatus.SAVE_FAILED,
                game_state,
            )
        return EquipmentActionResult(EquipmentActionStatus.EQUIPPED, candidate)

    @staticmethod
    def _target_can_manage(game_state, target_drifter_id):
        return can_manage_equipment_target(game_state, target_drifter_id)


__all__ = [
    "EquipmentActionResult",
    "EquipmentActionStatus",
    "EquipmentService",
    "can_manage_equipment_target",
    "equipment_target_members",
]

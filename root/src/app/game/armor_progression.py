"""Deterministic Hub armor investment transactions."""

from dataclasses import dataclass
from enum import StrEnum

from app.content.armor_progression_spec import (
    get_armor_upgrade_material,
    get_armor_upgrade_step,
    get_rarity_advancement,
)
from app.content.equipment_spec import MAX_ARMOR_UPGRADE_RANK
from app.game.game_state import GameState
from app.game.party_state import DungeonPhase
from app.persistence.save_port_contract import (
    SaveLoadStatus,
    SavePortError,
    is_save_port,
)


class ArmorProgressionStatus(StrEnum):
    UPGRADED = "upgraded"
    RARITY_ADVANCED = "rarity_advanced"
    INVALID_INSTANCE = "invalid_instance"
    NOT_ARMOR = "not_armor"
    NOT_AVAILABLE = "not_available"
    MAX_RANK = "max_rank"
    MAX_RARITY = "max_rarity"
    INSUFFICIENT_RESOURCES = "insufficient_resources"
    SAVE_FAILED = "save_failed"


@dataclass(frozen=True)
class ArmorProgressionResult:
    status: ArmorProgressionStatus
    game_state: GameState


@dataclass(frozen=True)
class ArmorProgressionPreview:
    action: str
    status: ArmorProgressionStatus
    instance_id: str | None
    current_rank: int | None
    next_rank: int | None
    current_rarity: str | None
    next_rarity: str | None
    gold_cost: int
    material_id: str | None
    material_quantity: int
    current_stat_bonuses: tuple[tuple[str, int], ...]
    projected_stat_bonuses: tuple[tuple[str, int], ...]
    can_apply: bool


class ArmorProgressionService:
    def __init__(self, *, save_port):
        if not is_save_port(save_port):
            raise TypeError("save_port must satisfy SavePort")
        self._save_port = save_port

    def upgrade_stat(self, game_state, *, instance_id):
        quote = self.preview_stat_upgrade(game_state, instance_id=instance_id)
        if not quote.can_apply:
            return ArmorProgressionResult(quote.status, game_state)
        instance = game_state.party_state.equipment_instance(instance_id)
        candidate = game_state.clone()
        party = candidate.party_state
        if not self._spend(
            party,
            gold=quote.gold_cost,
            materials={quote.material_id: quote.material_quantity},
        ):
            return ArmorProgressionResult(
                ArmorProgressionStatus.INSUFFICIENT_RESOURCES,
                game_state,
            )
        updated = instance.with_progression(upgrade_rank=instance.upgrade_rank + 1)
        party.replace_equipment_instance(updated)
        candidate._bind_equipment_state()
        return self._commit(candidate, game_state, ArmorProgressionStatus.UPGRADED)

    def advance_rarity(self, game_state, *, instance_id):
        quote = self.preview_rarity_advance(game_state, instance_id=instance_id)
        if not quote.can_apply:
            return ArmorProgressionResult(quote.status, game_state)
        instance = game_state.party_state.equipment_instance(instance_id)
        candidate = game_state.clone()
        party = candidate.party_state
        if not self._spend(
            party,
            gold=quote.gold_cost,
            materials={quote.material_id: quote.material_quantity},
        ):
            return ArmorProgressionResult(
                ArmorProgressionStatus.INSUFFICIENT_RESOURCES,
                game_state,
            )
        updated = instance.with_progression(rarity=quote.next_rarity)
        party.replace_equipment_instance(updated)
        candidate._bind_equipment_state()
        return self._commit(
            candidate,
            game_state,
            ArmorProgressionStatus.RARITY_ADVANCED,
        )

    @staticmethod
    def preview_stat_upgrade(game_state, *, instance_id):
        instance, status = ArmorProgressionService._eligible_armor(
            game_state,
            instance_id,
        )
        if status is not None:
            return _blocked_preview("stat_upgrade", status)
        current_stats = tuple(sorted(instance.stat_bonuses.items()))
        if instance.upgrade_rank >= MAX_ARMOR_UPGRADE_RANK:
            return _preview(
                "stat_upgrade",
                ArmorProgressionStatus.MAX_RANK,
                instance,
                gold_cost=0,
                material_id=None,
                material_quantity=0,
                next_rank=None,
                next_rarity=instance.rarity,
                current_stats=current_stats,
                projected_stats=current_stats,
            )
        step = get_armor_upgrade_step(instance.upgrade_rank + 1)
        material_id = get_armor_upgrade_material(instance.definition_id)
        projected = instance.with_progression(upgrade_rank=instance.upgrade_rank + 1)
        can_pay = _has_resources(
            game_state.party_state,
            gold=step.gold_cost,
            materials={material_id: step.material_quantity},
        )
        return _preview(
            "stat_upgrade",
            (
                ArmorProgressionStatus.UPGRADED
                if can_pay
                else ArmorProgressionStatus.INSUFFICIENT_RESOURCES
            ),
            instance,
            gold_cost=step.gold_cost,
            material_id=material_id,
            material_quantity=step.material_quantity,
            next_rank=instance.upgrade_rank + 1,
            next_rarity=instance.rarity,
            current_stats=current_stats,
            projected_stats=tuple(sorted(projected.stat_bonuses.items())),
        )

    @staticmethod
    def preview_rarity_advance(game_state, *, instance_id):
        instance, status = ArmorProgressionService._eligible_armor(
            game_state,
            instance_id,
        )
        if status is not None:
            return _blocked_preview("rarity_advance", status)
        current_stats = tuple(sorted(instance.stat_bonuses.items()))
        try:
            step = get_rarity_advancement(instance.rarity)
        except ValueError:
            return _preview(
                "rarity_advance",
                ArmorProgressionStatus.MAX_RARITY,
                instance,
                gold_cost=0,
                material_id=None,
                material_quantity=0,
                next_rank=instance.upgrade_rank,
                next_rarity=None,
                current_stats=current_stats,
                projected_stats=current_stats,
            )
        can_pay = _has_resources(
            game_state.party_state,
            gold=step.gold_cost,
            materials={step.material_id: step.material_quantity},
        )
        return _preview(
            "rarity_advance",
            (
                ArmorProgressionStatus.RARITY_ADVANCED
                if can_pay
                else ArmorProgressionStatus.INSUFFICIENT_RESOURCES
            ),
            instance,
            gold_cost=step.gold_cost,
            material_id=step.material_id,
            material_quantity=step.material_quantity,
            next_rank=instance.upgrade_rank,
            next_rarity=step.target_rarity,
            current_stats=current_stats,
            projected_stats=current_stats,
        )

    @staticmethod
    def _eligible_armor(game_state, instance_id):
        if not isinstance(game_state, GameState):
            raise TypeError("game_state must be a GameState")
        try:
            instance = game_state.party_state.equipment_instance(instance_id)
        except ValueError:
            return None, ArmorProgressionStatus.INVALID_INSTANCE
        if not instance.category == "armor":
            return None, ArmorProgressionStatus.NOT_ARMOR
        if (
            game_state.party_state.phase
            not in {DungeonPhase.HUB, DungeonPhase.PARTY_READY}
            or not instance.secured
        ):
            return None, ArmorProgressionStatus.NOT_AVAILABLE
        return instance, None

    @staticmethod
    def _spend(party, *, gold, materials):
        if not _has_resources(party, gold=gold, materials=materials):
            return False
        return party.spend_shared_gold(gold) and party.spend_shared_items(materials)

    def _commit(self, candidate, original, success_status):
        try:
            result = self._save_port.save(candidate)
        except (OSError, SavePortError, TypeError, ValueError):
            result = None
        if result is None or result.status is not SaveLoadStatus.SAVED:
            return ArmorProgressionResult(ArmorProgressionStatus.SAVE_FAILED, original)
        return ArmorProgressionResult(success_status, candidate)


def _has_resources(party, *, gold, materials):
    return not (
        party.shared_gold < gold
        or any(
            party.shared_items.get(item_id, 0) < quantity
            for item_id, quantity in materials.items()
        )
    )


def _preview(
    action,
    status,
    instance,
    *,
    gold_cost,
    material_id,
    material_quantity,
    next_rank,
    next_rarity,
    current_stats,
    projected_stats,
):
    return ArmorProgressionPreview(
        action,
        status,
        instance.instance_id,
        instance.upgrade_rank,
        next_rank,
        instance.rarity,
        next_rarity,
        gold_cost,
        material_id,
        material_quantity,
        current_stats,
        projected_stats,
        status
        in {
            ArmorProgressionStatus.UPGRADED,
            ArmorProgressionStatus.RARITY_ADVANCED,
        },
    )


def _blocked_preview(action, status):
    return ArmorProgressionPreview(
        action,
        status,
        None,
        None,
        None,
        None,
        None,
        0,
        None,
        0,
        (),
        (),
        False,
    )


__all__ = [
    "ArmorProgressionResult",
    "ArmorProgressionPreview",
    "ArmorProgressionService",
    "ArmorProgressionStatus",
]

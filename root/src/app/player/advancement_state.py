"""Permanent M3 advancement source state for one Drifter."""

from app.content.advancement_spec import (
    ADVANCEMENT_DRIFTER_IDS,
    AdvancementSkillKind,
    get_advancement_skill,
)
from app.combat.move import ResourceType


_EQUIPPED_NORMAL_MOVE_COUNT = 4


def move_id_for_name(drifter_id, move_name):
    parts = []
    pending_separator = False
    for character in move_name.lower():
        is_ascii_id_character = "a" <= character <= "z" or "0" <= character <= "9"
        if is_ascii_id_character:
            if pending_separator and parts:
                parts.append("_")
            parts.append(character)
            pending_separator = False
        else:
            pending_separator = True
    slug = "".join(parts)
    return f"{drifter_id}_starting_{slug}"


def move_ids_for_kit(drifter_id, moves):
    normal_move_ids = []
    super_move_ids = []
    for move in moves:
        if move.resource_type is ResourceType.SUPER:
            super_move_ids.append(move_id_for_name(drifter_id, move.name))
        else:
            normal_move_ids.append(move_id_for_name(drifter_id, move.name))
    return tuple(normal_move_ids), tuple(super_move_ids)


class AdvancementState:
    def __init__(
        self,
        drifter_id,
        starting_normal_move_ids,
        starting_super_move_ids,
    ):
        self._drifter_id = drifter_id
        self._starting_normal_move_ids = tuple(starting_normal_move_ids)
        self._starting_super_move_ids = tuple(starting_super_move_ids)
        has_tree = drifter_id in ADVANCEMENT_DRIFTER_IDS
        if has_tree and len(self._starting_normal_move_ids) != _EQUIPPED_NORMAL_MOVE_COUNT:
            raise ValueError("a Drifter must have exactly four starting normal moves")
        if len(set(self._starting_normal_move_ids)) != len(
            self._starting_normal_move_ids
        ):
            raise ValueError("starting normal move IDs must be unique")
        if has_tree and not self._starting_super_move_ids:
            raise ValueError("a Drifter must have a starting Super move")
        self._purchased_passive_skill_ids = []
        self._purchased_active_skill_ids = []
        self._equipped_normal_move_ids = list(self._starting_normal_move_ids)

    @property
    def purchased_passive_skill_ids(self):
        return tuple(self._purchased_passive_skill_ids)

    @property
    def starting_normal_move_ids(self):
        return self._starting_normal_move_ids

    @property
    def starting_super_move_ids(self):
        return self._starting_super_move_ids

    @property
    def purchased_active_skill_ids(self):
        return tuple(self._purchased_active_skill_ids)

    @property
    def equipped_normal_move_ids(self):
        return tuple(self._equipped_normal_move_ids)

    @property
    def available_normal_move_ids(self):
        return self._starting_normal_move_ids + tuple(
            skill_id
            for skill_id in self._purchased_active_skill_ids
            if get_advancement_skill(skill_id).kind
            in {
                AdvancementSkillKind.NORMAL_MOVE,
                AdvancementSkillKind.MANA_MOVE,
            }
        )

    @property
    def available_super_move_ids(self):
        return self._starting_super_move_ids + tuple(
            skill_id
            for skill_id in self._purchased_active_skill_ids
            if get_advancement_skill(skill_id).kind is AdvancementSkillKind.SUPER
        )

    def validate_purchase(self, skill_id, *, level, growth_points):
        skill = get_advancement_skill(skill_id)
        if skill.drifter_id != self._drifter_id:
            raise ValueError("advancement skill belongs to a different Drifter")
        purchased = (
            self._purchased_passive_skill_ids
            if skill.kind is AdvancementSkillKind.PASSIVE
            else self._purchased_active_skill_ids
        )
        if skill_id in purchased:
            raise ValueError("advancement skill already purchased")
        if level < skill.minimum_level:
            raise ValueError(
                f"advancement skill requires level {skill.minimum_level}"
            )
        if growth_points < skill.gp_cost:
            raise ValueError("insufficient Growth Points")
        return skill

    def record_purchase(self, skill):
        target = (
            self._purchased_passive_skill_ids
            if skill.kind is AdvancementSkillKind.PASSIVE
            else self._purchased_active_skill_ids
        )
        target.append(skill.skill_id)

    def equip_normal_move(self, move_id, *, slot):
        if isinstance(slot, bool) or not isinstance(slot, int):
            raise TypeError("normal move slot must be an integer")
        if not 0 <= slot < _EQUIPPED_NORMAL_MOVE_COUNT:
            raise ValueError("normal move slot is out of range")
        if move_id not in self.available_normal_move_ids:
            raise ValueError("normal move is not unlocked for this Drifter")
        previous = self._equipped_normal_move_ids[slot]
        self._equipped_normal_move_ids[slot] = move_id
        return previous

    def snapshot(self):
        return {
            "purchased_passive_skill_ids": list(
                self._purchased_passive_skill_ids
            ),
            "purchased_active_skill_ids": list(
                self._purchased_active_skill_ids
            ),
            "equipped_normal_move_ids": list(self._equipped_normal_move_ids),
        }

    @classmethod
    def from_snapshot(
        cls,
        drifter_id,
        starting_normal_move_ids,
        starting_super_move_ids,
        snapshot,
        *,
        level,
    ):
        if not isinstance(snapshot, dict):
            raise TypeError("advancement snapshot must be a mapping")
        expected = {
            "purchased_passive_skill_ids",
            "purchased_active_skill_ids",
            "equipped_normal_move_ids",
        }
        if set(snapshot) != expected:
            raise ValueError("advancement snapshot has an invalid shape")
        state = cls(
            drifter_id,
            starting_normal_move_ids,
            starting_super_move_ids,
        )
        passive_ids = _validate_id_list(
            snapshot["purchased_passive_skill_ids"],
            "purchased passive skill IDs",
        )
        active_ids = _validate_id_list(
            snapshot["purchased_active_skill_ids"],
            "purchased active skill IDs",
        )
        for skill_id in passive_ids:
            skill = get_advancement_skill(skill_id)
            if skill.drifter_id != drifter_id:
                raise ValueError("purchased passive belongs to a different Drifter")
            if skill.kind is not AdvancementSkillKind.PASSIVE:
                raise ValueError("purchased passive ID is not a passive skill")
            if level < skill.minimum_level:
                raise ValueError("purchased passive is above the Drifter's level")
        for skill_id in active_ids:
            skill = get_advancement_skill(skill_id)
            if skill.drifter_id != drifter_id:
                raise ValueError("purchased active skill belongs to a different Drifter")
            if skill.kind is AdvancementSkillKind.PASSIVE:
                raise ValueError("purchased active ID is not an active skill")
            if level < skill.minimum_level:
                raise ValueError("purchased active skill is above the Drifter's level")
        equipped = _validate_id_list(
            snapshot["equipped_normal_move_ids"],
            "equipped normal move IDs",
            allow_duplicates=True,
        )
        expected_count = (
            _EQUIPPED_NORMAL_MOVE_COUNT
            if drifter_id in ADVANCEMENT_DRIFTER_IDS
            else len(starting_normal_move_ids)
        )
        if len(equipped) != expected_count:
            raise ValueError("exactly four normal moves must be equipped")
        state._purchased_passive_skill_ids = list(passive_ids)
        state._purchased_active_skill_ids = list(active_ids)
        if not set(equipped).issubset(set(state.available_normal_move_ids)):
            raise ValueError("equipped move is not unlocked for this Drifter")
        state._equipped_normal_move_ids = list(equipped)
        return state


def _validate_id_list(values, name, *, allow_duplicates=False):
    if not isinstance(values, list):
        raise TypeError(f"{name} must be a list")
    if any(not isinstance(value, str) or not value for value in values):
        raise ValueError(f"{name} must contain non-empty strings")
    if not allow_duplicates and len(values) != len(set(values)):
        raise ValueError(f"{name} must be unique")
    return tuple(values)


__all__ = ["AdvancementState", "move_id_for_name", "move_ids_for_kit"]

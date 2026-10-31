"""Persistent shared party and dungeon progress state."""

from enum import StrEnum

from app.content.weapon_progression_spec import (
    MAX_CRAFTING_EXPERIENCE,
    crafting_level_for_experience,
)
from app.player.player_state import PlayerState


COMPANION_RECRUITMENT_COST = 65
_FLOOR_ONE_REPLAY_XP_RATES = (50, 40, 30, 20)
_FLOOR_ONE_MINIMUM_REPLAY_XP_RATE = 20


class DungeonPhase(StrEnum):
    OUTSIDE = "outside"
    HUB = "hub"
    PARTY_READY = "party_ready"
    OUTING = "outing"
    EXTRACTION = "extraction"
    COMPLETE = "complete"


class OutingRewards:
    def __init__(self, experience=0, gold=0, items=None):
        self._experience = _nonnegative("experience", experience)
        self._gold = _nonnegative("gold", gold)
        self._items = _item_stacks({} if items is None else items)

    @property
    def experience(self):
        return self._experience

    @property
    def gold(self):
        return self._gold

    @property
    def items(self):
        return dict(self._items)

    def snapshot(self):
        return {
            "experience": self.experience,
            "gold": self.gold,
            "items": self.items,
        }

    @classmethod
    def from_snapshot(cls, snapshot):
        return cls(
            experience=snapshot["experience"],
            gold=snapshot["gold"],
            items=snapshot["items"],
        )


class PartyState:
    def __init__(self):
        self._companions = ()
        self._active_drifter_ids = ()
        self._shared_gold = 0
        self._shared_items = {}
        self._crafting_experience = 0
        self._tutorial_complete = False
        self._phase = DungeonPhase.OUTSIDE
        self._outing_rewards = OutingRewards()
        self._floor_one_cleared = False
        self._floor_one_runs_started_after_clear = 0
        self._outing_xp_multiplier_percent = 100

    @property
    def companions(self):
        return self._companions

    @property
    def active_drifter_ids(self):
        return self._active_drifter_ids

    @property
    def shared_gold(self):
        return self._shared_gold

    @property
    def shared_items(self):
        return dict(self._shared_items)

    @property
    def crafting_experience(self):
        return self._crafting_experience

    @property
    def crafting_level(self):
        return crafting_level_for_experience(self.crafting_experience)

    def add_crafting_experience(self, amount):
        amount = _nonnegative("crafting experience", amount)
        old_level = self.crafting_level
        self._crafting_experience = min(
            MAX_CRAFTING_EXPERIENCE,
            self._crafting_experience + amount,
        )
        return self.crafting_level - old_level

    @property
    def tutorial_complete(self):
        return self._tutorial_complete

    @property
    def phase(self):
        return self._phase

    @property
    def outing_rewards(self):
        return self._outing_rewards

    @property
    def floor_one_cleared(self):
        return self._floor_one_cleared

    @property
    def floor_one_runs_started_after_clear(self):
        return self._floor_one_runs_started_after_clear

    @property
    def outing_xp_multiplier_percent(self):
        return self._outing_xp_multiplier_percent

    def arrive_at_hub(self, lead):
        _require_player_state(lead, "lead")
        if self._phase is not DungeonPhase.OUTSIDE:
            return False

        route_gold = lead.gold
        if not lead.spend_gold(route_gold):
            return False
        self._shared_gold += route_gold
        self._phase = DungeonPhase.HUB
        return True

    def recruit_companion(
        self,
        lead,
        companion,
        *,
        cost=COMPANION_RECRUITMENT_COST,
    ):
        _require_player_state(lead, "lead")
        _require_player_state(companion, "companion")
        lead_id = _drifter_id(lead)
        companion_id = _drifter_id(companion)
        cost = _nonnegative("recruitment cost", cost)
        if companion_id == lead_id:
            raise ValueError("the lead Drifter cannot be recruited as a companion")
        if any(_drifter_id(member) == companion_id for member in self._companions):
            raise ValueError("the Drifter was already recruited")
        if self._phase is not DungeonPhase.HUB:
            raise ValueError("a companion can only be recruited at the hub")
        if len(self._companions) >= 3:
            raise ValueError("the permanent roster is full")
        if self._shared_gold < cost:
            return False

        first_companion = not self._companions
        self._shared_gold -= cost
        self._companions = self._companions + (companion,)
        if first_companion and not self._tutorial_complete:
            self._set_active_drifter_ids((lead_id, companion_id))
            self._phase = DungeonPhase.PARTY_READY
        return True

    def select_active_pair(self, drifter_ids, *, recruited_ids):
        if self._phase is not DungeonPhase.HUB:
            raise ValueError("the active pair can only change at the Hub")
        if not isinstance(drifter_ids, (tuple, list)) or len(drifter_ids) != 2:
            raise ValueError("an active pair must contain exactly two Drifters")
        if not isinstance(recruited_ids, (tuple, list)):
            raise TypeError("recruited_ids must be a sequence of canonical IDs")
        selected = tuple(_canonical_id(value, "active Drifter ID") for value in drifter_ids)
        recruited = tuple(
            _canonical_id(value, "recruited Drifter ID")
            for value in recruited_ids
        )
        if len(recruited) != len(set(recruited)):
            raise ValueError("recruited Drifter IDs must be unique")
        if len(selected) != len(set(selected)):
            raise ValueError("an active pair cannot contain the same Drifter twice")
        if any(drifter_id not in recruited for drifter_id in selected):
            raise ValueError("an active Drifter must be recruited")
        self._set_active_drifter_ids(selected)

    def _set_active_drifter_ids(self, drifter_ids):
        values = tuple(_canonical_id(value, "active Drifter ID") for value in drifter_ids)
        if not 1 <= len(values) <= 2:
            raise ValueError("the active party must contain one or two Drifters")
        if len(values) != len(set(values)):
            raise ValueError("active Drifter IDs must be unique")
        self._active_drifter_ids = values

    def add_shared_gold(self, amount):
        self._shared_gold += _nonnegative("gold amount", amount)

    def add_shared_items(self, items):
        additions = _item_stacks(items)
        for item_id, quantity in additions.items():
            self._shared_items[item_id] = (
                self._shared_items.get(item_id, 0) + quantity
            )

    def spend_shared_items(self, costs):
        costs = _item_stacks(costs)
        if any(
            self._shared_items.get(item_id, 0) < quantity
            for item_id, quantity in costs.items()
        ):
            return False
        remaining = dict(self._shared_items)
        for item_id, quantity in costs.items():
            balance = remaining[item_id] - quantity
            if balance:
                remaining[item_id] = balance
            else:
                del remaining[item_id]
        self._shared_items = remaining
        return True

    def begin_outing(self):
        if self._phase is not DungeonPhase.PARTY_READY:
            return False
        self._outing_rewards = OutingRewards()
        self._phase = DungeonPhase.OUTING
        return True

    def start_floor_one_run(self):
        if not self.tutorial_complete:
            raise ValueError("the tutorial must be complete before Floor 1")
        if self._phase is not DungeonPhase.HUB:
            raise ValueError("a Floor 1 run can only start from the Hub")
        if len(self._active_drifter_ids) != 2:
            raise ValueError("a Floor 1 run requires the two-Drifter party")

        rate = 100
        if self.floor_one_cleared:
            rate = _FLOOR_ONE_REPLAY_XP_RATES[
                min(
                    self._floor_one_runs_started_after_clear,
                    len(_FLOOR_ONE_REPLAY_XP_RATES) - 1,
                )
            ]
            rate = max(rate, _FLOOR_ONE_MINIMUM_REPLAY_XP_RATE)
            self._floor_one_runs_started_after_clear += 1

        self._outing_rewards = OutingRewards()
        self._outing_xp_multiplier_percent = rate
        self._phase = DungeonPhase.OUTING
        return rate

    def add_floor_one_rewards(self, *, experience, gold, items=None):
        if not self.tutorial_complete or self._phase is not DungeonPhase.OUTING:
            raise ValueError("Floor 1 rewards require an active dangerous run")
        rewards = OutingRewards(experience, gold, items)
        current = self._outing_rewards
        combined_items = current.items
        for item_id, quantity in rewards.items.items():
            combined_items[item_id] = combined_items.get(item_id, 0) + quantity
        self._outing_rewards = OutingRewards(
            current.experience + rewards.experience,
            current.gold + rewards.gold,
            combined_items,
        )

    def begin_floor_one_extraction(self, *, partial):
        if not isinstance(partial, bool):
            raise TypeError("partial must be a boolean")
        if not self.tutorial_complete or self._phase is not DungeonPhase.OUTING:
            return False

        party_size = len(self._active_drifter_ids)
        if party_size != 2:
            raise ValueError("Floor 1 extraction requires the two-Drifter party")
        denominator = 100 * party_size * (2 if partial else 1)
        experience_each = (
            self._outing_rewards.experience
            * self.outing_xp_multiplier_percent
            // denominator
        )
        experience = experience_each * party_size
        gold = self._outing_rewards.gold
        if partial:
            gold = (gold + 1) // 2
        self._outing_rewards = OutingRewards(
            experience=experience,
            gold=gold,
            items=self._outing_rewards.items,
        )
        self._phase = DungeonPhase.EXTRACTION
        return True

    def complete_floor_one_boss(self, party_members):
        if not self.tutorial_complete or self._phase is not DungeonPhase.OUTING:
            return False
        self._validate_party_members(party_members)
        rewards = self._floor_one_payout(partial=False)
        self._bank_rewards(party_members, rewards)
        self._floor_one_cleared = True
        self._outing_rewards = OutingRewards()
        self._outing_xp_multiplier_percent = 100
        self._phase = DungeonPhase.HUB
        return True

    def fail_floor_one_run(self, party_members):
        if not self.tutorial_complete or self._phase is not DungeonPhase.OUTING:
            return False
        self._validate_party_members(party_members)
        self._outing_rewards = OutingRewards()
        self._restore_party(party_members)
        self._outing_xp_multiplier_percent = 100
        self._phase = DungeonPhase.HUB
        return True

    def cancel_outing_start(self):
        if self._phase is not DungeonPhase.OUTING:
            return False
        self._outing_rewards = OutingRewards()
        self._phase = DungeonPhase.PARTY_READY
        return True

    def begin_extraction(self, *, experience, gold, items=None):
        if self._phase is not DungeonPhase.OUTING:
            return False
        rewards = OutingRewards(experience, gold, items)
        party_size = len(self._active_drifter_ids)
        if party_size < 1 or rewards.experience % party_size:
            raise ValueError("outing experience must divide evenly across the party")
        self._outing_rewards = rewards
        self._phase = DungeonPhase.EXTRACTION
        return True

    def complete_extraction(self, party_members):
        if self._phase is not DungeonPhase.EXTRACTION:
            return False
        self._validate_party_members(party_members)

        rewards = self._outing_rewards
        self._bank_rewards(party_members, rewards)
        self._tutorial_complete = True
        self._outing_rewards = OutingRewards()
        self._outing_xp_multiplier_percent = 100
        self._phase = DungeonPhase.HUB
        return True

    def reset_failed_tutorial(self, party_members):
        if self._phase is not DungeonPhase.OUTING:
            return False
        self._validate_party_members(party_members)
        self._outing_rewards = OutingRewards()
        self._restore_party(party_members)
        self._phase = DungeonPhase.PARTY_READY
        return True

    @classmethod
    def from_snapshot(cls, snapshot, *, companions, active_drifter_ids=None):
        state = cls()
        state._companions = tuple(companions)
        if active_drifter_ids is None:
            active_drifter_ids = snapshot.get("active_drifter_ids")
        if active_drifter_ids is not None:
            state._set_active_drifter_ids(active_drifter_ids)
        state._shared_gold = _nonnegative("shared_gold", snapshot["shared_gold"])
        state._shared_items = _item_stacks(snapshot["shared_items"])
        state._crafting_experience = _nonnegative(
            "crafting_experience",
            snapshot.get("crafting_experience", 0),
        )
        if state._crafting_experience > MAX_CRAFTING_EXPERIENCE:
            raise ValueError("crafting experience exceeds the level-100 cap")
        state._tutorial_complete = snapshot["tutorial_complete"]
        state._phase = DungeonPhase(snapshot["phase"])
        state._outing_rewards = OutingRewards.from_snapshot(
            snapshot["outing_rewards"]
        )
        state._floor_one_cleared = snapshot.get("floor_one_cleared", False)
        if not isinstance(state._floor_one_cleared, bool):
            raise ValueError("floor_one_cleared must be a boolean")
        state._floor_one_runs_started_after_clear = _nonnegative(
            "floor_one_runs_started_after_clear",
            snapshot.get("floor_one_runs_started_after_clear", 0),
        )
        if (
            state._floor_one_runs_started_after_clear
            and not state._floor_one_cleared
        ):
            raise ValueError("Floor 1 replay runs require a cleared floor")
        state._outing_xp_multiplier_percent = _nonnegative(
            "outing_xp_multiplier_percent",
            snapshot.get("outing_xp_multiplier_percent", 100),
        )
        if state._outing_xp_multiplier_percent not in {20, 30, 40, 50, 100}:
            raise ValueError("outing XP multiplier is not an authored rate")
        active_floor_one_run = (
            state._tutorial_complete
            and state._phase in {DungeonPhase.OUTING, DungeonPhase.EXTRACTION}
        )
        if active_floor_one_run:
            expected_rate = 100
            if state._floor_one_cleared:
                expected_rate = _FLOOR_ONE_REPLAY_XP_RATES[
                    min(
                        max(state._floor_one_runs_started_after_clear - 1, 0),
                        len(_FLOOR_ONE_REPLAY_XP_RATES) - 1,
                    )
                ]
            if state._outing_xp_multiplier_percent != expected_rate:
                raise ValueError("active Floor 1 run has an inconsistent XP rate")
        elif state._outing_xp_multiplier_percent != 100:
            raise ValueError("inactive Floor 1 runs must use the default XP rate")
        snapshot_party_size = (
            len(state._active_drifter_ids)
            if state._active_drifter_ids
            else 1 + len(state._companions)
        )
        if state._phase is DungeonPhase.EXTRACTION and (
            state._outing_rewards.experience % snapshot_party_size
        ):
            raise ValueError("outing experience must divide evenly across the party")
        return state

    def snapshot(self):
        snapshot = {
            "companions": [member.snapshot() for member in self.companions],
            "active_drifter_ids": list(self.active_drifter_ids),
            "shared_gold": self.shared_gold,
            "shared_items": self.shared_items,
            "crafting_experience": self.crafting_experience,
            "tutorial_complete": self.tutorial_complete,
            "phase": self.phase.value,
            "outing_rewards": self.outing_rewards.snapshot(),
            "floor_one_cleared": self.floor_one_cleared,
            "floor_one_runs_started_after_clear": (
                self.floor_one_runs_started_after_clear
            ),
            "outing_xp_multiplier_percent": (
                self.outing_xp_multiplier_percent
            ),
        }
        return snapshot

    def _validate_party_members(self, party_members):
        if not isinstance(party_members, tuple) or len(party_members) != 2:
            raise TypeError("Floor 1 requires the two-member tutorial party")
        if not all(isinstance(member, PlayerState) for member in party_members):
            raise TypeError("party_members must contain PlayerState values")
        if tuple(_drifter_id(member) for member in party_members) != self._active_drifter_ids:
            raise ValueError("party_members do not match the active party")

    def _floor_one_payout(self, *, partial):
        party_size = len(self._active_drifter_ids)
        denominator = 100 * party_size * (2 if partial else 1)
        experience_each = (
            self._outing_rewards.experience
            * self.outing_xp_multiplier_percent
            // denominator
        )
        gold = self._outing_rewards.gold
        if partial:
            gold = (gold + 1) // 2
        return OutingRewards(
            experience=experience_each * party_size,
            gold=gold,
            items=self._outing_rewards.items,
        )

    def _bank_rewards(self, party_members, rewards):
        experience_each = rewards.experience // len(party_members)
        for member in party_members:
            member.exp_state.validate_gain_amount(experience_each)
        for member in party_members:
            member.gain_experience(experience_each)
        self._restore_party(party_members)
        self._shared_gold += rewards.gold
        for item_id, quantity in rewards.items.items():
            self._shared_items[item_id] = self._shared_items.get(item_id, 0) + quantity

    @staticmethod
    def _restore_party(party_members):
        for member in party_members:
            member.health.heal(member.health.maximum)
            member.mana_resource.restore(member.mana_resource.maximum)


def _require_player_state(value, name):
    if not isinstance(value, PlayerState):
        raise TypeError(f"{name} must be a PlayerState")


def _drifter_id(player_state):
    profile = player_state.character.profile
    drifter_id = getattr(profile, "drifter_id", None)
    if drifter_id is None:
        raise ValueError("party members must have canonical Drifter profiles")
    return _canonical_id(drifter_id, "Drifter ID")


def _canonical_id(value, name):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _nonnegative(name, value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 0:
        raise ValueError(f"{name} must not be negative")
    return value


def _item_stacks(items):
    if not isinstance(items, dict):
        raise TypeError("items must be a mapping of item IDs to quantities")
    normalized = {}
    for item_id, quantity in items.items():
        if not isinstance(item_id, str) or not item_id:
            raise ValueError("item IDs must be non-empty strings")
        if isinstance(quantity, bool) or not isinstance(quantity, int):
            raise TypeError("item quantities must be integers")
        if quantity <= 0:
            raise ValueError("item quantities must be positive")
        normalized[item_id] = quantity
    return normalized


__all__ = [
    "COMPANION_RECRUITMENT_COST",
    "DungeonPhase",
    "OutingRewards",
    "PartyState",
]

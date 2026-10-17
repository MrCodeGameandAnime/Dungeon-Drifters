"""Persistent shared party and dungeon progress state."""

from enum import StrEnum

from app.player.player_state import PlayerState


COMPANION_RECRUITMENT_COST = 65


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
        self._shared_gold = 0
        self._shared_items = {}
        self._tutorial_complete = False
        self._phase = DungeonPhase.OUTSIDE
        self._outing_rewards = OutingRewards()

    @property
    def companions(self):
        return self._companions

    @property
    def shared_gold(self):
        return self._shared_gold

    @property
    def shared_items(self):
        return dict(self._shared_items)

    @property
    def tutorial_complete(self):
        return self._tutorial_complete

    @property
    def phase(self):
        return self._phase

    @property
    def outing_rewards(self):
        return self._outing_rewards

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

    def recruit_companion(self, lead, companion):
        _require_player_state(lead, "lead")
        _require_player_state(companion, "companion")
        lead_id = _drifter_id(lead)
        companion_id = _drifter_id(companion)
        if companion_id == lead_id:
            raise ValueError("the lead Drifter cannot be recruited as a companion")
        if any(_drifter_id(member) == companion_id for member in self._companions):
            raise ValueError("the Drifter was already recruited")
        if self._phase is not DungeonPhase.HUB:
            raise ValueError("a companion can only be recruited at the hub")
        if self._companions:
            raise ValueError("the tutorial party already has a companion")
        if self._shared_gold < COMPANION_RECRUITMENT_COST:
            return False

        self._shared_gold -= COMPANION_RECRUITMENT_COST
        self._companions = self._companions + (companion,)
        self._phase = DungeonPhase.PARTY_READY
        return True

    def add_shared_gold(self, amount):
        self._shared_gold += _nonnegative("gold amount", amount)

    def begin_outing(self):
        if self._phase is not DungeonPhase.PARTY_READY:
            return False
        self._outing_rewards = OutingRewards()
        self._phase = DungeonPhase.OUTING
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
        if rewards.experience % (1 + len(self._companions)):
            raise ValueError("outing experience must divide evenly across the party")
        self._outing_rewards = rewards
        self._phase = DungeonPhase.EXTRACTION
        return True

    def complete_extraction(self, party_members):
        if self._phase is not DungeonPhase.EXTRACTION:
            return False
        if not isinstance(party_members, tuple) or len(party_members) != 2:
            raise TypeError("extraction requires the two-member tutorial party")
        if not all(isinstance(member, PlayerState) for member in party_members):
            raise TypeError("party_members must contain PlayerState values")
        if party_members[1] is not self._companions[0]:
            raise ValueError("party_members do not match the recruited party")

        rewards = self._outing_rewards
        experience_each = rewards.experience // len(party_members)
        for member in party_members:
            member.exp_state.validate_gain_amount(experience_each)
        for member in party_members:
            member.gain_experience(experience_each)
            member.health.heal(member.health.maximum)
            member.mana_resource.restore(member.mana_resource.maximum)

        self._shared_gold += rewards.gold
        for item_id, quantity in rewards.items.items():
            self._shared_items[item_id] = self._shared_items.get(item_id, 0) + quantity
        self._tutorial_complete = True
        self._outing_rewards = OutingRewards()
        self._phase = DungeonPhase.HUB
        return True

    def reset_failed_tutorial(self):
        if self._phase is not DungeonPhase.OUTING:
            return False
        self._companions = ()
        self._shared_gold = 0
        self._shared_items = {}
        self._tutorial_complete = False
        self._outing_rewards = OutingRewards()
        self._phase = DungeonPhase.OUTSIDE
        return True

    @classmethod
    def from_snapshot(cls, snapshot, *, companions):
        state = cls()
        state._companions = tuple(companions)
        state._shared_gold = _nonnegative("shared_gold", snapshot["shared_gold"])
        state._shared_items = _item_stacks(snapshot["shared_items"])
        state._tutorial_complete = snapshot["tutorial_complete"]
        state._phase = DungeonPhase(snapshot["phase"])
        state._outing_rewards = OutingRewards.from_snapshot(
            snapshot["outing_rewards"]
        )
        if state._phase is DungeonPhase.EXTRACTION and (
            state._outing_rewards.experience % (1 + len(state._companions))
        ):
            raise ValueError("outing experience must divide evenly across the party")
        return state

    def snapshot(self):
        return {
            "companions": [member.snapshot() for member in self.companions],
            "shared_gold": self.shared_gold,
            "shared_items": self.shared_items,
            "tutorial_complete": self.tutorial_complete,
            "phase": self.phase.value,
            "outing_rewards": self.outing_rewards.snapshot(),
        }


def _require_player_state(value, name):
    if not isinstance(value, PlayerState):
        raise TypeError(f"{name} must be a PlayerState")


def _drifter_id(player_state):
    profile = player_state.character.profile
    if profile is None:
        raise ValueError("party members must have canonical Drifter profiles")
    return profile.choice


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

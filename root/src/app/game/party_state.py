"""Persistent shared party and dungeon progress state."""

from enum import StrEnum
from uuid import UUID, uuid4

from app.content.permanent_discovery_spec import (
    is_valid_permanent_discovery_source_id,
)
from app.content.weapon_progression_spec import (
    MAX_CRAFTING_EXPERIENCE,
    crafting_level_for_experience,
)
from app.player.player_state import PlayerState
from app.items.equipment import EquipmentInstance
from app.items.armor_modifier import ArmorModifierInstance
from app.player.scaling import secured_xp_bonus_bps_from_intuition
from app.content.hub_economy import get_supply_item
from app.game.floor_two_boss_helper import (
    floor_two_replay_requires_available_helper,
)
from app.snapshot import to_plain_value


COMPANION_RECRUITMENT_COST = 65
MAX_CARRIED_SUPPLY_UNITS = 6
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
        self._equipment_instances = []
        self._modifier_instances = []
        self._shared_gold = 0
        self._shared_items = {}
        self._carried_items = {}
        self._crafting_experience = 0
        self._tutorial_complete = False
        self._phase = DungeonPhase.OUTSIDE
        self._outing_rewards = OutingRewards()
        self._floor_one_cleared = False
        self._floor_one_runs_started_after_clear = 0
        self._outing_xp_multiplier_percent = 100
        self._floor_two_cleared = False
        self._floor_two_runs_started_after_clear = 0
        self._floor_two_run_id = None
        self._floor_two_outing_xp_multiplier_percent = 100
        self._resolved_run_events = []

    @property
    def companions(self):
        return self._companions

    @property
    def active_drifter_ids(self):
        return self._active_drifter_ids

    @property
    def equipment_instances(self):
        return tuple(self._equipment_instances)

    def add_equipment_instance(self, instance):
        if not isinstance(instance, EquipmentInstance):
            raise TypeError("instance must be an EquipmentInstance")
        if any(
            existing.instance_id == instance.instance_id
            for existing in self._equipment_instances
        ):
            raise ValueError("equipment instance ID is already owned")
        self._equipment_instances.append(instance)
        return instance

    def equipment_instance(self, instance_id):
        for instance in self._equipment_instances:
            if instance.instance_id == instance_id:
                return instance
        raise ValueError(f"equipment instance is not owned: {instance_id}")

    def replace_equipment_instance(self, instance):
        if not isinstance(instance, EquipmentInstance):
            raise TypeError("instance must be an EquipmentInstance")
        for index, existing in enumerate(self._equipment_instances):
            if existing.instance_id == instance.instance_id:
                self._equipment_instances[index] = instance
                return instance
        raise ValueError(f"equipment instance is not owned: {instance.instance_id}")

    @property
    def modifier_instances(self):
        return tuple(self._modifier_instances)

    def add_modifier_instance(self, instance):
        if not isinstance(instance, ArmorModifierInstance):
            raise TypeError("instance must be an ArmorModifierInstance")
        if any(
            existing.instance_id == instance.instance_id
            for existing in self._modifier_instances
        ):
            raise ValueError("modifier instance ID is already owned")
        if any(
            item.instance_id == instance.instance_id
            for item in self._equipment_instances
        ):
            raise ValueError("modifier ID collides with an equipment instance")
        self._modifier_instances.append(instance)
        return instance

    def modifier_instance(self, instance_id):
        for instance in self._modifier_instances:
            if instance.instance_id == instance_id:
                return instance
        raise ValueError(f"modifier instance is not owned: {instance_id}")

    def remove_modifier_instance(self, instance_id):
        for index, instance in enumerate(self._modifier_instances):
            if instance.instance_id == instance_id:
                return self._modifier_instances.pop(index)
        raise ValueError(f"modifier instance is not owned: {instance_id}")

    def remove_equipment_instance(self, instance_id):
        for index, instance in enumerate(self._equipment_instances):
            if instance.instance_id == instance_id:
                return self._equipment_instances.pop(index)
        raise ValueError(f"equipment instance is not owned: {instance_id}")

    def secure_outing_equipment(self):
        if self._phase not in {DungeonPhase.OUTING, DungeonPhase.EXTRACTION}:
            return False
        self._secure_unsecured_equipment()
        return True

    @property
    def shared_gold(self):
        return self._shared_gold

    @property
    def shared_items(self):
        return dict(self._shared_items)

    @property
    def carried_items(self):
        return dict(self._carried_items)

    @property
    def carried_item_units(self):
        return sum(self._carried_items.values())

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

    @property
    def floor_two_cleared(self):
        return self._floor_two_cleared

    @property
    def floor_two_runs_started_after_clear(self):
        return self._floor_two_runs_started_after_clear

    @property
    def floor_two_run_id(self):
        return self._floor_two_run_id

    @property
    def floor_two_boss_reward_committed(self):
        return self._floor_two_run_id is not None and any(
            event["run_id"] == self._floor_two_run_id
            and event["node_id"] == "floor_two_battle_10"
            and event["kind"] == "encounter_rewards"
            for event in self._resolved_run_events
        )

    @property
    def floor_two_outing_xp_multiplier_percent(self):
        return self._floor_two_outing_xp_multiplier_percent

    @property
    def floor_two_boss_helper_id(self):
        run_id = self._floor_two_run_id
        if run_id is None:
            return None
        for event in self._resolved_run_events:
            if (
                event["run_id"] == run_id
                and event["kind"] == "boss_helper_selection"
            ):
                return event["result"]["drifter_id"]
        return None

    @property
    def resolved_run_events(self):
        return tuple(to_plain_value(event, "party.resolved_run_events") for event in self._resolved_run_events)

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

    def recruit_floor_two_companion(
        self,
        companion,
        *,
        recruited_ids,
        cost=COMPANION_RECRUITMENT_COST,
    ):
        _require_player_state(companion, "companion")
        if self._floor_two_run_id is None or self._phase is not DungeonPhase.OUTING:
            raise ValueError("Floor 2 recruitment requires an active run")
        if not isinstance(recruited_ids, (tuple, list)):
            raise TypeError("recruited_ids must be a sequence of canonical IDs")
        roster_ids = tuple(
            _canonical_id(value, "recruited Drifter ID")
            for value in recruited_ids
        )
        if len(roster_ids) != len(set(roster_ids)):
            raise ValueError("recruited Drifter IDs must be unique")
        companion_id = _drifter_id(companion)
        if companion_id in roster_ids:
            raise ValueError("the Drifter was already recruited")
        if len(roster_ids) >= 4:
            raise ValueError("the permanent roster is full")
        if not set(self._active_drifter_ids).issubset(roster_ids):
            raise ValueError("active Drifters must belong to the recruited roster")
        cost = _nonnegative("recruitment cost", cost)
        if self._shared_gold < cost:
            return False

        self._shared_gold -= cost
        self._companions = self._companions + (companion,)
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

    def spend_shared_gold(self, amount):
        amount = _nonnegative("gold amount", amount)
        if self._shared_gold < amount:
            return False
        self._shared_gold -= amount
        return True

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

    def load_carried_supplies(self, items):
        if self._phase not in {DungeonPhase.HUB, DungeonPhase.PARTY_READY}:
            return False
        items = _item_stacks(items)
        if any(
            (spec := get_supply_item(item_id)) is None or not spec.carryable
            for item_id in items
        ):
            return False
        if self.carried_item_units + sum(items.values()) > MAX_CARRIED_SUPPLY_UNITS:
            return False
        if not self.spend_shared_items(items):
            return False
        for item_id, quantity in items.items():
            self._carried_items[item_id] = (
                self._carried_items.get(item_id, 0) + quantity
            )
        return True

    def consume_carried_supplies(self, costs):
        costs = _item_stacks(costs)
        if any(
            self._carried_items.get(item_id, 0) < quantity
            for item_id, quantity in costs.items()
        ):
            return False
        remaining = dict(self._carried_items)
        for item_id, quantity in costs.items():
            balance = remaining[item_id] - quantity
            if balance:
                remaining[item_id] = balance
            else:
                del remaining[item_id]
        self._carried_items = remaining
        return True

    def restore_carried_supplies_checkpoint(self, items):
        checkpoint = _item_stacks(items)
        if sum(checkpoint.values()) > MAX_CARRIED_SUPPLY_UNITS:
            raise ValueError("carried supplies exceed the six-unit capacity")
        if any(
            (spec := get_supply_item(item_id)) is None or not spec.carryable
            for item_id in checkpoint
        ):
            raise ValueError("carried supplies must contain only carryable items")
        self._carried_items = checkpoint

    def use_healing_potion(self, target, *, deployed_members):
        if self._phase not in {
            DungeonPhase.HUB,
            DungeonPhase.PARTY_READY,
            DungeonPhase.OUTING,
        }:
            return False
        if not self._is_floor_two_helper_party(deployed_members):
            self._validate_party_members(deployed_members)
        if not isinstance(target, PlayerState) or not any(
            target is member for member in deployed_members
        ):
            return False
        item = get_supply_item("healing_potion")
        if (
            item is None
            or item.healing_percent <= 0
            or not target.health.is_alive()
            or target.health.current >= target.health.maximum
            or self._carried_items.get(item.item_id, 0) < 1
        ):
            return False
        amount = target.health.maximum * item.healing_percent // 100
        if amount <= 0:
            return False
        if not self.consume_carried_supplies({item.item_id: 1}):
            return False
        target.health.heal(amount)
        return True

    def _is_floor_two_helper_party(self, party_members):
        if (
            not isinstance(party_members, tuple)
            or len(party_members) != 3
            or self._phase is not DungeonPhase.OUTING
            or self._floor_two_run_id is None
        ):
            return False
        helper_id = self.floor_two_boss_helper_id
        return (
            helper_id is not None
            and tuple(_drifter_id(member) for member in party_members)
            == self._active_drifter_ids + (helper_id,)
        )

    def unload_carried_supplies(self, items):
        if self._phase not in {DungeonPhase.HUB, DungeonPhase.PARTY_READY}:
            return False
        items = _item_stacks(items)
        if any(
            (spec := get_supply_item(item_id)) is None or not spec.carryable
            for item_id in items
        ):
            return False
        if not self.consume_carried_supplies(items):
            return False
        for item_id, quantity in items.items():
            self._shared_items[item_id] = self._shared_items.get(item_id, 0) + quantity
        return True

    def return_carried_supplies(self):
        self.add_shared_items(self._carried_items)
        self._carried_items = {}

    def discard_carried_supplies(self):
        self._carried_items = {}

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

    def start_floor_two_run(self, *, run_id_factory=uuid4):
        if not callable(run_id_factory):
            raise TypeError("run_id_factory must be callable")
        if not self.tutorial_complete or not self.floor_one_cleared:
            raise ValueError("Floor 1 must be cleared before Floor 2")
        if self._phase is not DungeonPhase.HUB:
            raise ValueError("a Floor 2 run can only start from the Hub")
        if len(self._active_drifter_ids) != 2:
            raise ValueError("a Floor 2 run requires the two-Drifter party")
        if (
            self.floor_two_cleared
            and floor_two_replay_requires_available_helper(
                self._active_drifter_ids
            )
        ):
            raise ValueError(
                "a Floor 2 replay requires an active pair that leaves D3 or D4 available"
            )
        run_id = run_id_factory()
        if isinstance(run_id, UUID):
            run_id = str(run_id)
        if not _valid_run_id(run_id):
            raise ValueError("run ID must be a non-empty lowercase token")
        rate = 100
        if self.floor_two_cleared:
            rate = _FLOOR_ONE_REPLAY_XP_RATES[
                min(
                    self._floor_two_runs_started_after_clear,
                    len(_FLOOR_ONE_REPLAY_XP_RATES) - 1,
                )
            ]
            rate = max(rate, _FLOOR_ONE_MINIMUM_REPLAY_XP_RATE)
            self._floor_two_runs_started_after_clear += 1

        self._floor_two_run_id = run_id
        self._floor_two_outing_xp_multiplier_percent = rate
        self._outing_rewards = OutingRewards()
        self._phase = DungeonPhase.OUTING
        return rate

    def add_floor_two_rewards(self, *, experience, gold, items=None):
        if self._floor_two_run_id is None or self._phase is not DungeonPhase.OUTING:
            raise ValueError("Floor 2 rewards require an active Floor 2 run")
        self._add_outing_rewards(experience=experience, gold=gold, items=items)

    def record_run_event(self, event):
        normalized = _run_event(event)
        if normalized["run_id"] != self._floor_two_run_id:
            raise ValueError("run event must belong to the active Floor 2 run")
        existing = self.run_event(normalized["event_key"])
        if existing is not None:
            if existing != normalized:
                raise ValueError("run event key was reused with a different outcome")
            return False
        candidate_events = list(self._resolved_run_events)
        candidate_events.append(normalized)
        validate_run_event_history(
            candidate_events,
            active_drifter_ids=self._active_drifter_ids,
            active_run_id=self._floor_two_run_id,
            require_complete=False,
        )
        self._resolved_run_events.append(normalized)
        return True

    def run_event(self, event_key):
        for event in self._resolved_run_events:
            if event["event_key"] == event_key:
                return to_plain_value(event, "party.run_event")
        return None

    def select_floor_two_boss_helper(self, drifter_id, *, node_id):
        if self._floor_two_run_id is None or self._phase is not DungeonPhase.OUTING:
            raise ValueError("a Floor 2 helper requires an active outing")
        if node_id != "floor_two_pre_boss_rest":
            raise ValueError("a Floor 2 helper must be selected at the pre-boss Rest")
        event = {
            "event_key": _run_event_key(
                self._floor_two_run_id,
                node_id,
                "boss_helper_selection",
            ),
            "run_id": self._floor_two_run_id,
            "floor_id": "floor_two",
            "node_id": node_id,
            "kind": "boss_helper_selection",
            "position": None,
            "result": {"drifter_id": drifter_id},
        }
        return self.record_run_event(event)

    def fail_floor_two_run(self, party_members, *, recruited_members=None):
        if self._floor_two_run_id is None or self._phase is not DungeonPhase.OUTING:
            return False
        self._validate_party_members(party_members)
        equipment_members = self._equipment_members(
            party_members,
            recruited_members,
        )
        self._discard_unsecured_equipment(equipment_members)
        self._outing_rewards = OutingRewards()
        self.discard_carried_supplies()
        self._restore_party(party_members)
        self._floor_two_run_id = None
        self._floor_two_outing_xp_multiplier_percent = 100
        self._resolved_run_events = []
        self._phase = DungeonPhase.HUB
        return True

    def complete_floor_two_boss(self, party_members):
        if self._floor_two_run_id is None or self._phase is not DungeonPhase.OUTING:
            return False
        self._validate_party_members(party_members)
        rewards = self._outing_rewards
        party_size = len(self._active_drifter_ids)
        experience_each = (
            rewards.experience
            * self._floor_two_outing_xp_multiplier_percent
            // (100 * party_size)
        )
        payout = OutingRewards(
            experience=experience_each * party_size,
            gold=rewards.gold,
            items=rewards.items,
        )
        self._bank_rewards(party_members, payout)
        self._secure_unsecured_equipment()
        self.return_carried_supplies()
        self._floor_two_cleared = True
        self._outing_rewards = OutingRewards()
        self._floor_two_run_id = None
        self._floor_two_outing_xp_multiplier_percent = 100
        self._resolved_run_events = []
        self._phase = DungeonPhase.HUB
        return True

    def begin_floor_two_extraction(self, *, partial):
        if not isinstance(partial, bool):
            raise TypeError("partial must be a boolean")
        if self._floor_two_run_id is None or self._phase is not DungeonPhase.OUTING:
            return False
        if len(self._active_drifter_ids) != 2:
            raise ValueError("Floor 2 extraction requires the two-Drifter party")
        self._outing_rewards = self._floor_two_payout(partial=partial)
        self._phase = DungeonPhase.EXTRACTION
        return True

    def complete_floor_two_extraction(
        self,
        party_members,
    ):
        if (
            self._floor_two_run_id is None
            or self._phase is not DungeonPhase.EXTRACTION
        ):
            return False
        self._validate_party_members(party_members)
        self._bank_rewards(party_members, self._outing_rewards)
        self._secure_unsecured_equipment()
        self.return_carried_supplies()
        self._outing_rewards = OutingRewards()
        self._floor_two_run_id = None
        self._floor_two_outing_xp_multiplier_percent = 100
        self._resolved_run_events = []
        self._phase = DungeonPhase.HUB
        return True

    def _add_outing_rewards(self, *, experience, gold, items=None):
        additions = OutingRewards(experience, gold, items)
        current = self._outing_rewards
        combined_items = current.items
        for item_id, quantity in additions.items.items():
            combined_items[item_id] = combined_items.get(item_id, 0) + quantity
        self._outing_rewards = OutingRewards(
            current.experience + additions.experience,
            current.gold + additions.gold,
            combined_items,
        )

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
        floor_two_extraction = self._floor_two_run_id is not None
        rewards = (
            self._floor_two_payout(partial=False)
            if floor_two_extraction
            else self._floor_one_payout(partial=False)
        )
        self._bank_rewards(party_members, rewards)
        self._secure_unsecured_equipment()
        self.return_carried_supplies()
        self._floor_one_cleared = True
        self._outing_rewards = OutingRewards()
        self._outing_xp_multiplier_percent = 100
        self._phase = DungeonPhase.HUB
        return True

    def fail_floor_one_run(self, party_members, *, recruited_members=None):
        if not self.tutorial_complete or self._phase is not DungeonPhase.OUTING:
            return False
        self._validate_party_members(party_members)
        equipment_members = self._equipment_members(
            party_members,
            recruited_members,
        )
        self._discard_unsecured_equipment(equipment_members)
        self._outing_rewards = OutingRewards()
        self.discard_carried_supplies()
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
        self._secure_unsecured_equipment()
        self.return_carried_supplies()
        self._tutorial_complete = True
        self._outing_rewards = OutingRewards()
        self._outing_xp_multiplier_percent = 100
        self._phase = DungeonPhase.HUB
        return True

    def return_with_talisman(self, party_members, *, recruited_members=None):
        if (
            not self.tutorial_complete
            or self._phase is not DungeonPhase.OUTING
            or self._carried_items.get("return_talisman", 0) < 1
        ):
            return False
        self._validate_party_members(party_members)
        floor_two_run = self._floor_two_run_id is not None
        rewards = (
            self._floor_two_payout(partial=False)
            if floor_two_run
            else self._floor_one_payout(partial=False)
        )
        experience_awards = self.secured_xp_awards(
            party_members,
            rewards.experience,
        )
        equipment_members = self._equipment_members(
            party_members,
            recruited_members,
        )
        if not self.consume_carried_supplies({"return_talisman": 1}):
            return False

        self._discard_unsecured_equipment(equipment_members)
        self._bank_rewards(
            party_members,
            OutingRewards(experience=rewards.experience, gold=0, items={}),
            experience_awards=experience_awards,
        )
        self.return_carried_supplies()
        self._outing_rewards = OutingRewards()
        self._outing_xp_multiplier_percent = 100
        if floor_two_run:
            self._floor_two_run_id = None
            self._floor_two_outing_xp_multiplier_percent = 100
            self._resolved_run_events = []
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
        raw_equipment = snapshot.get("equipment_instances", [])
        if not isinstance(raw_equipment, list):
            raise TypeError("equipment_instances must be a list")
        state._equipment_instances = [
            EquipmentInstance.from_snapshot(item)
            for item in raw_equipment
        ]
        instance_ids = tuple(
            item.instance_id for item in state._equipment_instances
        )
        if len(instance_ids) != len(set(instance_ids)):
            raise ValueError("equipment instance IDs must be unique")
        raw_modifiers = snapshot.get("modifier_instances", [])
        if not isinstance(raw_modifiers, list):
            raise TypeError("modifier_instances must be a list")
        state._modifier_instances = [
            ArmorModifierInstance.from_snapshot(item)
            for item in raw_modifiers
        ]
        modifier_ids = tuple(item.instance_id for item in state._modifier_instances)
        if len(modifier_ids) != len(set(modifier_ids)):
            raise ValueError("modifier instance IDs must be unique")
        if set(instance_ids) & set(modifier_ids):
            raise ValueError("equipment and modifier instance IDs must be unique")
        if active_drifter_ids is None:
            active_drifter_ids = snapshot.get("active_drifter_ids")
        if active_drifter_ids is not None:
            state._set_active_drifter_ids(active_drifter_ids)
        state._shared_gold = _nonnegative("shared_gold", snapshot["shared_gold"])
        state._shared_items = _item_stacks(snapshot["shared_items"])
        state._carried_items = _item_stacks(snapshot.get("carried_items", {}))
        if sum(state._carried_items.values()) > MAX_CARRIED_SUPPLY_UNITS:
            raise ValueError("carried supplies exceed the six-unit capacity")
        if any(
            (spec := get_supply_item(item_id)) is None or not spec.carryable
            for item_id in state._carried_items
        ):
            raise ValueError("carried supplies must contain only carryable items")
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
        state._floor_two_cleared = snapshot.get("floor_two_cleared", False)
        if not isinstance(state._floor_two_cleared, bool):
            raise ValueError("floor_two_cleared must be a boolean")
        state._floor_two_runs_started_after_clear = _nonnegative(
            "floor_two_runs_started_after_clear",
            snapshot.get("floor_two_runs_started_after_clear", 0),
        )
        if state._floor_two_runs_started_after_clear and not state._floor_two_cleared:
            raise ValueError("Floor 2 replay runs require a cleared floor")
        state._floor_two_run_id = snapshot.get("floor_two_run_id")
        if state._floor_two_run_id is not None and not _valid_run_id(
            state._floor_two_run_id
        ):
            raise ValueError("floor_two_run_id is invalid")
        state._floor_two_outing_xp_multiplier_percent = _nonnegative(
            "floor_two_outing_xp_multiplier_percent",
            snapshot.get("floor_two_outing_xp_multiplier_percent", 100),
        )
        if state._floor_two_outing_xp_multiplier_percent not in {20, 30, 40, 50, 100}:
            raise ValueError("Floor 2 outing XP multiplier is not an authored rate")
        raw_events = snapshot.get("resolved_run_events", [])
        if not isinstance(raw_events, list):
            raise TypeError("resolved_run_events must be a list")
        state._resolved_run_events = [_run_event(event) for event in raw_events]
        validate_run_event_history(
            state._resolved_run_events,
            active_drifter_ids=state._active_drifter_ids,
            active_run_id=state._floor_two_run_id,
        )
        if state._floor_two_run_id is None:
            state._resolved_run_events = []
        else:
            state._resolved_run_events = [
                event
                for event in state._resolved_run_events
                if event["run_id"] == state._floor_two_run_id
            ]
        active_floor_two_run = state._floor_two_run_id is not None
        if active_floor_two_run:
            if not state._floor_two_cleared and state._floor_two_runs_started_after_clear:
                raise ValueError("active Floor 2 run has inconsistent replay state")
            if state._phase not in {
                DungeonPhase.OUTING,
                DungeonPhase.EXTRACTION,
            } or not state.tutorial_complete:
                raise ValueError(
                    "active Floor 2 run must be an outing or extraction after tutorial"
                )
            expected_rate = 100
            if state._floor_two_cleared:
                expected_rate = _FLOOR_ONE_REPLAY_XP_RATES[
                    min(
                        max(state._floor_two_runs_started_after_clear - 1, 0),
                        len(_FLOOR_ONE_REPLAY_XP_RATES) - 1,
                    )
                ]
            if state._floor_two_outing_xp_multiplier_percent != expected_rate:
                raise ValueError("active Floor 2 run has an inconsistent XP rate")
        elif state._floor_two_outing_xp_multiplier_percent != 100:
            raise ValueError("inactive Floor 2 runs must use the default XP rate")
        active_floor_one_run = (
            state._tutorial_complete
            and state._phase in {DungeonPhase.OUTING, DungeonPhase.EXTRACTION}
            and state._floor_two_run_id is None
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
            "equipment_instances": [
                item.snapshot() for item in self.equipment_instances
            ],
            "modifier_instances": [
                item.snapshot() for item in self.modifier_instances
            ],
            "active_drifter_ids": list(self.active_drifter_ids),
            "shared_gold": self.shared_gold,
            "shared_items": self.shared_items,
            "carried_items": self.carried_items,
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
            "floor_two_cleared": self.floor_two_cleared,
            "floor_two_runs_started_after_clear": (
                self.floor_two_runs_started_after_clear
            ),
            "floor_two_run_id": self.floor_two_run_id,
            "floor_two_outing_xp_multiplier_percent": (
                self.floor_two_outing_xp_multiplier_percent
            ),
            "resolved_run_events": list(self.resolved_run_events),
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

    def _floor_two_payout(self, *, partial):
        party_size = len(self._active_drifter_ids)
        denominator = 100 * party_size * (2 if partial else 1)
        experience_each = (
            self._outing_rewards.experience
            * self._floor_two_outing_xp_multiplier_percent
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

    def secured_xp_awards(self, party_members, secured_experience):
        if not party_members:
            raise ValueError("secured XP requires at least one eligible Drifter")
        experience_each = secured_experience // len(party_members)
        awards = []
        for member in party_members:
            intuition_bonus_bps = secured_xp_bonus_bps_from_intuition(
                member.effective_stat("intuition")
            )
            award = experience_each + (
                experience_each * intuition_bonus_bps // 10000
            )
            member.exp_state.validate_gain_amount(award)
            awards.append(award)
        return tuple(awards)

    def _bank_rewards(self, party_members, rewards, *, experience_awards=None):
        if experience_awards is None:
            experience_awards = self.secured_xp_awards(
                party_members,
                rewards.experience,
            )
        elif len(experience_awards) != len(party_members):
            raise ValueError("secured XP awards must match eligible Drifters")
        for member, award in zip(party_members, experience_awards):
            member.exp_state.validate_gain_amount(award)
        for member, award in zip(party_members, experience_awards):
            member.gain_experience(award)
        self._restore_party(party_members)
        self._shared_gold += rewards.gold
        for item_id, quantity in rewards.items.items():
            self._shared_items[item_id] = self._shared_items.get(item_id, 0) + quantity

    def _secure_unsecured_equipment(self):
        self._equipment_instances = [
            item if item.secured else item.with_security(secured=True)
            for item in self._equipment_instances
        ]

    def _discard_unsecured_equipment(self, members):
        lost_ids = {
            item.instance_id
            for item in self._equipment_instances
            if not item.secured
        }
        if not lost_ids:
            return
        for member in members:
            refs = member.equipped_equipment_ids
            changed = False
            for slot_id, instance_id in refs.items():
                if instance_id in lost_ids:
                    refs[slot_id] = None
                    changed = True
            if changed:
                member._set_equipped_equipment_ids(refs)
        self._equipment_instances = [
            item
            for item in self._equipment_instances
            if item.instance_id not in lost_ids
        ]

    def _equipment_members(self, party_members, recruited_members):
        if recruited_members is None:
            members = tuple(party_members) + self._companions
        else:
            if not isinstance(recruited_members, (tuple, list)):
                raise TypeError("recruited_members must be a sequence")
            members = tuple(recruited_members)
        if any(not isinstance(member, PlayerState) for member in members):
            raise TypeError("recruited_members must contain PlayerState values")
        unique = []
        seen = set()
        for member in members:
            identity = id(member)
            if identity not in seen:
                seen.add(identity)
                unique.append(member)
        if any(id(member) not in seen for member in party_members):
            raise ValueError("recruited_members must include the active party")
        return tuple(unique)

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


def _valid_run_id(value):
    return (
        isinstance(value, str)
        and 1 <= len(value) <= 80
        and (value[0].islower() or value[0].isdigit())
        and all(character.islower() or character.isdigit() or character in "-_" for character in value)
    )


def _run_event(value):
    if not isinstance(value, dict):
        raise TypeError("run event must be a mapping")
    expected = {
        "event_key",
        "run_id",
        "floor_id",
        "node_id",
        "kind",
        "position",
        "result",
    }
    if set(value) != expected:
        raise ValueError("run event has an invalid shape")
    if not _valid_run_id(value["run_id"]):
        raise ValueError("run event ID is invalid")
    if value["floor_id"] != "floor_two":
        raise ValueError("run event floor is invalid")
    if not _valid_event_part(value["node_id"]):
        raise ValueError("run event node_id is invalid")
    if value["kind"] not in {
        "enemy_drop",
        "encounter_rewards",
        "discovery_search",
        "armor_reward",
        "boss_helper_selection",
    }:
        raise ValueError("run event kind is invalid")
    position = value["position"]
    if position is not None and (
        isinstance(position, bool) or not isinstance(position, int) or position < 0
    ):
        raise ValueError("run event position is invalid")
    if not isinstance(value["result"], dict):
        raise TypeError("run event result must be a mapping")
    expected_position = value["kind"] == "enemy_drop"
    if expected_position != (position is not None):
        raise ValueError("run event position does not match its kind")
    event_key = _run_event_key(
        value["run_id"],
        value["node_id"],
        value["kind"],
        position,
    )
    if value["event_key"] != event_key:
        raise ValueError("run event key is inconsistent with its identity")
    _validate_run_event_result(value["kind"], value["result"], value)
    return to_plain_value(value, "party.run_event")


def _validate_run_event_result(kind, result, event):
    if kind == "enemy_drop":
        if set(result) != {"entries", "items"}:
            raise ValueError("enemy-drop event result has an invalid shape")
        if not isinstance(result["entries"], list):
            raise TypeError("enemy-drop entries must be a list")
        item_totals = {}
        for entry in result["entries"]:
            if not isinstance(entry, dict) or set(entry) != {
                "item_id", "quantity", "chance_bps", "roll", "awarded"
            }:
                raise ValueError("enemy-drop entry has an invalid shape")
            if not _valid_event_part(entry["item_id"]):
                raise ValueError("enemy-drop item ID is invalid")
            _positive("enemy-drop quantity", entry["quantity"])
            chance = _nonnegative("enemy-drop chance", entry["chance_bps"])
            roll = _nonnegative("enemy-drop roll", entry["roll"])
            if chance > 10000 or not 1 <= roll <= 10000:
                raise ValueError("enemy-drop chance or roll is outside its range")
            if not isinstance(entry["awarded"], bool):
                raise TypeError("enemy-drop awarded must be a boolean")
            awarded = roll <= chance
            if entry["awarded"] is not awarded:
                raise ValueError("enemy-drop result disagrees with its roll")
            if awarded:
                item_totals[entry["item_id"]] = (
                    item_totals.get(entry["item_id"], 0) + entry["quantity"]
                )
        if _event_item_stacks(result["items"]) != item_totals:
            raise ValueError("enemy-drop item totals disagree with entry outcomes")
        return

    if kind == "armor_reward":
        if set(result) != {"template_id", "floor", "source_id", "instance"}:
            raise ValueError("armor reward result has an invalid shape")
        if not _valid_event_part(result["template_id"]):
            raise ValueError("armor reward template ID is invalid")
        if type(result["floor"]) is not int or result["floor"] != 2:
            raise ValueError("armor reward floor is invalid")
        if not _valid_event_part(result["source_id"]):
            raise ValueError("armor reward source ID is invalid")
        try:
            instance = EquipmentInstance.from_snapshot(result["instance"])
        except (TypeError, ValueError, KeyError) as error:
            raise ValueError("armor reward instance is invalid") from error
        if (
            instance.definition_id != result["template_id"]
            or instance.source_id != result["source_id"]
            or instance.secured
            or instance.category != "armor"
        ):
            raise ValueError("armor reward instance disagrees with its authored outcome")
        return

    if kind == "boss_helper_selection":
        if set(result) != {"drifter_id"}:
            raise ValueError("boss-helper result has an invalid shape")
        if result["drifter_id"] not in {"zhaivra", "joruun"}:
            raise ValueError("boss-helper Drifter ID is invalid")
        return

    if kind == "encounter_rewards":
        if set(result) != {
            "experience", "gold", "items", "enemy_count", "drop_event_keys"
        }:
            raise ValueError("encounter reward result has an invalid shape")
        _nonnegative("encounter experience", result["experience"])
        _nonnegative("encounter gold", result["gold"])
        _positive("encounter enemy count", result["enemy_count"])
        items = _event_item_stacks(result["items"])
        keys = result["drop_event_keys"]
        if not isinstance(keys, list) or len(keys) != result["enemy_count"]:
            raise ValueError("encounter reward event keys do not match enemy count")
        expected_keys = [
            _run_event_key(event["run_id"], event["node_id"], "enemy_drop", index)
            for index in range(result["enemy_count"])
        ]
        if keys != expected_keys:
            raise ValueError("encounter reward event keys are invalid")
        if any(not _valid_event_part(item_id) for item_id in items):
            raise ValueError("encounter reward item ID is invalid")
        return

    if set(result) != {
        "source_id",
        "searcher_drifter_id",
        "effective_chance_bps",
        "roll",
        "found",
    }:
        raise ValueError("discovery search result has an invalid shape")
    if not is_valid_permanent_discovery_source_id(result["source_id"]):
        raise ValueError("discovery source ID is invalid")
    if not _valid_event_part(result["searcher_drifter_id"]):
        raise ValueError("discovery searcher ID is invalid")
    chance = _nonnegative("discovery chance", result["effective_chance_bps"])
    roll = _nonnegative("discovery roll", result["roll"])
    if chance > 10000 or not 1 <= roll <= 10000:
        raise ValueError("discovery chance or roll is outside its range")
    if not isinstance(result["found"], bool):
        raise TypeError("discovery found must be a boolean")
    if result["found"] is not (roll <= chance):
        raise ValueError("discovery outcome disagrees with its roll")


def _event_item_stacks(items):
    if not isinstance(items, dict):
        raise TypeError("event item totals must be a mapping")
    normalized = {}
    for item_id, quantity in items.items():
        if not isinstance(item_id, str) or not item_id:
            raise ValueError("event item ID must be a non-empty string")
        normalized[item_id] = _positive("event item quantity", quantity)
    return normalized


def _valid_event_part(value):
    return (
        isinstance(value, str)
        and 1 <= len(value) <= 80
        and "a" <= value[0] <= "z"
        and all("a" <= char <= "z" or "0" <= char <= "9" or char == "_" for char in value)
    )


def _run_event_key(run_id, node_id, kind, position=None):
    key = f"floor_two:{run_id}:{node_id}:{kind}"
    if position is not None:
        key += f":{position}"
    return key


def _positive(name, value):
    value = _nonnegative(name, value)
    if value == 0:
        raise ValueError(f"{name} must be positive")
    return value


def validate_run_event(value):
    return _run_event(value)


def validate_run_event_history(
    events,
    *,
    active_drifter_ids=None,
    active_run_id=None,
    require_complete=True,
):
    if not isinstance(events, (tuple, list)):
        raise TypeError("resolved run events must be a sequence")
    normalized = tuple(_run_event(event) for event in events)
    by_key = {event["event_key"]: event for event in normalized}
    if len(by_key) != len(normalized):
        raise ValueError("resolved run event keys must be unique")

    from app.content.catalog import (
        get_known_permanent_discovery_source,
        get_permanent_discovery_search_node_id,
        get_route_node_spec,
        is_known_floor_two_route_node_id,
    )
    from app.content.route_spec import RouteNodeKind

    for event in normalized:
        node_id = event["node_id"]
        if not is_known_floor_two_route_node_id(node_id):
            raise ValueError("run event references an unknown Floor 2 route node")
        node = get_route_node_spec(node_id)
        if event["kind"] in {"enemy_drop", "encounter_rewards", "armor_reward"}:
            if (
                node.kind not in {RouteNodeKind.COMBAT, RouteNodeKind.BOSS}
                or node.encounter_id is None
            ):
                raise ValueError("combat event references a non-encounter route node")
        elif event["kind"] == "discovery_search":
            result = event["result"]
            try:
                source = get_known_permanent_discovery_source(result["source_id"])
            except ValueError as error:
                raise ValueError("discovery event references an unknown source") from error
            if get_permanent_discovery_search_node_id(result["source_id"]) != node_id:
                raise ValueError("discovery source does not belong to this route node")
            if (
                event["run_id"] == active_run_id
                and active_drifter_ids is not None
                and result["searcher_drifter_id"] not in active_drifter_ids
            ):
                raise ValueError("discovery searcher is not in the active party")
        elif event["kind"] == "boss_helper_selection":
            if node_id != "floor_two_pre_boss_rest":
                raise ValueError("boss-helper selection is outside its route checkpoint")
            helper_id = event["result"]["drifter_id"]
            if (
                event["run_id"] == active_run_id
                and active_drifter_ids is not None
                and helper_id in active_drifter_ids
            ):
                raise ValueError("boss helper duplicates an active Drifter")

    referenced_drop_keys = set()
    for event in normalized:
        if event["kind"] != "encounter_rewards":
            continue
        result = event["result"]
        drop_events = [by_key.get(key) for key in result["drop_event_keys"]]
        if any(drop is None for drop in drop_events):
            raise ValueError("encounter reward evidence is missing an enemy drop")
        aggregate = {}
        for drop in drop_events:
            if (
                drop["kind"] != "enemy_drop"
                or drop["run_id"] != event["run_id"]
                or drop["node_id"] != event["node_id"]
            ):
                raise ValueError("encounter reward references unrelated drop evidence")
            referenced_drop_keys.add(drop["event_key"])
            for item_id, quantity in drop["result"]["items"].items():
                aggregate[item_id] = aggregate.get(item_id, 0) + quantity
        if aggregate != result["items"]:
            raise ValueError("encounter rewards disagree with enemy drop evidence")

    actual_drop_keys = {
        event["event_key"] for event in normalized if event["kind"] == "enemy_drop"
    }
    if require_complete and actual_drop_keys != referenced_drop_keys:
        raise ValueError("enemy drop evidence must belong to a resolved encounter")
    return normalized


__all__ = [
    "COMPANION_RECRUITMENT_COST",
    "MAX_CARRIED_SUPPLY_UNITS",
    "DungeonPhase",
    "OutingRewards",
    "PartyState",
    "validate_run_event",
    "validate_run_event_history",
]

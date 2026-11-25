"""Small portable expedition persistence and UTC-clock state."""

import time
from uuid import UUID

from app.snapshot import to_plain_value


MAX_EXPEDITION_ENERGY = 100
EXPEDITION_REGENERATION_SECONDS = 9 * 60
EXPEDITION_DURATION_SECONDS = 20 * 60
EXPEDITION_LAUNCH_COST = 10
FLOOR_IDS = (
    "floor_one", "floor_two", "floor_three", "floor_four", "floor_five",
)
ASSIGNMENT_CATEGORIES = (
    "training", "material", "equipment", "recovery", "scouting", "story",
    "elite",
)
_LEGACY_ASSIGNMENT_KEYS = {
    "assignment_id", "outing_floor_id", "destination_floor_id", "category",
    "expedition_drifter_ids", "started_at_utc", "last_observed_at_utc",
    "completed_at_utc",
}
_ASSIGNMENT_KEYS = _LEGACY_ASSIGNMENT_KEYS | {
    "frozen_outcome", "report_content_id"
}
_LEGACY_REPORT_KEYS = {
    "report_id", "outing_floor_id", "destination_floor_id", "category",
    "expedition_drifter_ids", "started_at_utc", "completed_at_utc",
    "secured_base_xp", "experience_awards", "reward_item_id",
    "reward_quantity", "claimed",
}
_REPORT_KEYS = _LEGACY_REPORT_KEYS | {"frozen_outcome", "report_content_id"}
FLOOR_FIVE_APPROACH_OUTING_ID = "floor_five_approach"
FLOOR_FIVE_REUNION_OUTING_ID = "floor_five_reunion"
_SCOUTING_FACT_IDS = (
    "m8_fact_reliquary_threats",
    "m8_fact_ashen_vault",
    "m8_fact_ashen_regent",
)
_REPORT_CONTENT_IDS = {
    ("floor_four", "material"): "m8_floor_four_material_report",
    ("floor_four", "equipment"): "m8_floor_four_equipment_report",
    ("floor_four", "recovery"): "m8_floor_four_recovery_report",
    ("floor_four", "scouting"): "m8_floor_four_scouting_report",
    ("floor_four", "story"): "m8_floor_four_story_report",
    ("floor_four", "elite"): "m8_floor_four_elite_report",
    ("floor_five", "material"): "m8_floor_five_material_report",
}


def is_expeditions_unlocked(game_state):
    return (
        game_state.party_state.tutorial_complete
        and game_state.party_state.floor_three_cleared
        and len(game_state.recruited_members) == 4
    )


def category_unavailable_reason(destination_floor_id, category, *, game_state=None):
    if destination_floor_id not in FLOOR_IDS:
        return "This destination has no eligible authored reward source."
    if category == "training":
        return None
    if category == "material":
        if destination_floor_id in FLOOR_IDS[:3]:
            return None
        if destination_floor_id == "floor_four":
            return (
                None
                if _has_authored_drop_source(
                    "floor_four", "m8_floor_four_metal_drop_01", "grade_iv_metal"
                )
                else "No eligible authored Grade-IV Metal source exists on Floor IV."
            )
        if game_state is None or not game_state.party_state.floor_five_cleared:
            return "Complete Floor V before selecting its Material report."
        if not _floor_five_material_source_ids():
            return "No eligible authored Floor-V Grade-IV Core source exists."
        return None
    if destination_floor_id != "floor_four":
        return "No eligible authored reward source exists for this category."
    if category == "equipment":
        try:
            from app.content.catalog import get_armor_reward_source

            source = get_armor_reward_source("m8_floor_four_armor_source")
        except ValueError:
            source = None
        return (
            None
            if source is not None and source.floor_id == destination_floor_id
            else "No eligible authored equipment reward exists for this floor."
        )
    if category == "recovery":
        try:
            from app.content.catalog import get_fixed_item_reward_source

            source = get_fixed_item_reward_source("m8_floor_four_recovery_source")
        except ValueError:
            source = None
        return (
            None
            if source is not None and source.floor_id == destination_floor_id
            else "No eligible authored recovery item exists for this floor."
        )
    if category == "scouting":
        return None
    if category == "story":
        return None
    if category == "elite":
        return (
            None
            if _has_authored_drop_source(
                "floor_four", "m8_floor_four_core_drop_01", "grade_iv_cores"
            )
            else "No eligible authored Grade-IV Core source exists on Floor IV."
        )
    return "That expedition category is not available."


def report_content_id_for(destination_floor_id, category):
    return _REPORT_CONTENT_IDS.get((destination_floor_id, category))


class ExpeditionState:
    def __init__(self):
        self._energy = MAX_EXPEDITION_ENERGY
        self._energy_anchor_utc = None
        self._active_assignment = None
        self._reports = []

    @property
    def energy(self):
        return self._energy

    @property
    def energy_anchor_utc(self):
        return self._energy_anchor_utc

    @property
    def active_assignment(self):
        return to_plain_value(
            self._active_assignment,
            "expedition.active_assignment",
        )

    @property
    def reports(self):
        return tuple(to_plain_value(self._reports, "expedition.reports"))

    def preview_energy(self, now):
        now = _utc_second(now)
        anchor = _parse_utc(self._energy_anchor_utc)
        if anchor is None or now < anchor:
            return self._energy
        if self._energy == MAX_EXPEDITION_ENERGY:
            return self._energy
        gained = (now - anchor) // EXPEDITION_REGENERATION_SECONDS
        return min(MAX_EXPEDITION_ENERGY, self._energy + gained)

    def update_energy(self, now):
        now = _utc_second(now)
        anchor = _parse_utc(self._energy_anchor_utc)
        if anchor is None:
            self._energy_anchor_utc = _format_utc(now)
            return self._energy
        if now < anchor:
            return self._energy
        if self._energy == MAX_EXPEDITION_ENERGY:
            self._energy_anchor_utc = _format_utc(now)
            return self._energy

        gained = (now - anchor) // EXPEDITION_REGENERATION_SECONDS
        if gained <= 0:
            return self._energy
        self._energy = min(MAX_EXPEDITION_ENERGY, self._energy + gained)
        if self._energy == MAX_EXPEDITION_ENERGY:
            self._energy_anchor_utc = _format_utc(now)
        else:
            self._energy_anchor_utc = _format_utc(
                anchor + gained * EXPEDITION_REGENERATION_SECONDS
            )
        return self._energy

    def spend_energy(self, amount, *, now):
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("energy spend must be a positive integer")
        candidate = ExpeditionState.from_snapshot(self.snapshot())
        candidate.update_energy(now)
        if candidate.energy < amount:
            return False
        candidate._energy -= amount
        self._energy = candidate._energy
        self._energy_anchor_utc = candidate._energy_anchor_utc
        return True

    def observe_assignment_time(self, now):
        if self._active_assignment is None:
            return False
        now = _utc_second(now)
        assignment = self._active_assignment
        last_seen = _parse_utc(assignment["last_observed_at_utc"])
        start = _parse_utc(assignment["started_at_utc"])
        effective = max(now, last_seen)
        changed = effective > last_seen
        if changed:
            assignment["last_observed_at_utc"] = _format_utc(effective)
        if (
            assignment["completed_at_utc"] is None
            and effective >= start + EXPEDITION_DURATION_SECONDS
        ):
            assignment["completed_at_utc"] = _format_utc(
                start + EXPEDITION_DURATION_SECONDS
            )
            changed = True
        return changed

    def assignment_remaining_seconds(self, now):
        if self._active_assignment is None:
            return None
        assignment = self._active_assignment
        if assignment["completed_at_utc"] is not None:
            return 0
        now = max(
            _utc_second(now),
            _parse_utc(assignment["last_observed_at_utc"]),
        )
        deadline = (
            _parse_utc(assignment["started_at_utc"])
            + EXPEDITION_DURATION_SECONDS
        )
        return max(0, deadline - now)

    def install_assignment(self, assignment):
        if self._active_assignment is not None:
            raise ValueError("an expedition assignment is already active")
        _validate_assignment(assignment)
        if any(report["report_id"] == assignment["assignment_id"] for report in self._reports):
            raise ValueError("expedition assignment ID has already been settled")
        self._active_assignment = to_plain_value(
            assignment,
            "expedition.assignment",
        )

    def settle_assignment(self, report=None):
        assignment = self._active_assignment
        if assignment is None:
            return False
        if report is not None:
            _validate_report(report)
            if report["report_id"] != assignment["assignment_id"]:
                raise ValueError("expedition report does not match active assignment")
            if any(existing["report_id"] == report["report_id"] for existing in self._reports):
                raise ValueError("expedition report already exists")
            self._reports.append(to_plain_value(report, "expedition.report"))
        self._active_assignment = None
        return True

    def mark_report_claimed(self, report_id):
        for report in self._reports:
            if report["report_id"] == report_id:
                if report["claimed"]:
                    return False
                report["claimed"] = True
                return True
        return False

    def snapshot(self):
        return {
            "energy": self.energy,
            "energy_anchor_utc": self.energy_anchor_utc,
            "active_assignment": self.active_assignment,
            "reports": list(self.reports),
        }

    def clone(self):
        clone = type(self)()
        clone._energy = self._energy
        clone._energy_anchor_utc = self._energy_anchor_utc
        clone._active_assignment = to_plain_value(
            self._active_assignment,
            "expedition.active_assignment",
        )
        clone._reports = to_plain_value(self._reports, "expedition.reports")
        return clone

    @classmethod
    def from_snapshot(cls, snapshot, *, allow_legacy_shape=False):
        if not isinstance(snapshot, dict):
            raise TypeError("expedition state must be an object")
        if set(snapshot) != {"energy", "energy_anchor_utc", "active_assignment", "reports"}:
            raise ValueError("expedition state has an invalid shape")
        energy = snapshot["energy"]
        if isinstance(energy, bool) or not isinstance(energy, int):
            raise TypeError("expedition energy must be an integer")
        if not 0 <= energy <= MAX_EXPEDITION_ENERGY:
            raise ValueError("expedition energy is outside its allowed range")
        _parse_utc(snapshot["energy_anchor_utc"])
        assignment = snapshot["active_assignment"]
        if assignment is not None:
            _validate_assignment(
                assignment,
                allow_legacy_shape=allow_legacy_shape,
            )
        reports = snapshot["reports"]
        if not isinstance(reports, list):
            raise TypeError("expedition reports must be a list")
        for report in reports:
            _validate_report(report, allow_legacy_shape=allow_legacy_shape)
        report_ids = [report["report_id"] for report in reports]
        if len(report_ids) != len(set(report_ids)):
            raise ValueError("expedition report IDs must be unique")
        if assignment is not None and assignment["assignment_id"] in report_ids:
            raise ValueError("active expedition assignment was already settled")
        state = cls()
        state._energy = energy
        state._energy_anchor_utc = snapshot["energy_anchor_utc"]
        state._active_assignment = to_plain_value(
            assignment,
            "expedition.active_assignment",
        )
        state._reports = to_plain_value(reports, "expedition.reports")
        return state


def _validate_assignment(value, *, allow_legacy_shape=False):
    keys = set(value) if isinstance(value, dict) else set()
    legacy = allow_legacy_shape and keys == _LEGACY_ASSIGNMENT_KEYS
    if not isinstance(value, dict) or keys != _ASSIGNMENT_KEYS and not legacy:
        raise ValueError("active expedition assignment has an invalid shape")
    _validate_uuid(value["assignment_id"], "assignment ID")
    _validate_outing_floor(value["outing_floor_id"])
    _validate_floor(value["destination_floor_id"])
    if value["outing_floor_id"] in {"floor_three", FLOOR_FIVE_REUNION_OUTING_ID}:
        raise ValueError("expeditions cannot accompany a Floor III outing")
    allowed_categories = ("training", "material") if legacy else ASSIGNMENT_CATEGORIES
    if value["category"] not in allowed_categories:
        raise ValueError("expedition category is unavailable")
    if not legacy:
        expected_content_id = report_content_id_for(
            value["destination_floor_id"], value["category"]
        )
        if value["report_content_id"] != expected_content_id:
            raise ValueError("expedition report content ID is invalid")
        _validate_frozen_outcome(
            value["category"],
            value["destination_floor_id"],
            value["frozen_outcome"],
        )
    _validate_drifter_ids(value["expedition_drifter_ids"])
    started = _parse_utc(value["started_at_utc"])
    observed = _parse_utc(value["last_observed_at_utc"])
    if started is None or observed is None or observed < started:
        raise ValueError("expedition assignment timestamps are inconsistent")
    completed_value = value["completed_at_utc"]
    if completed_value is not None:
        completed = _parse_utc(completed_value)
        if completed != started + EXPEDITION_DURATION_SECONDS:
            raise ValueError("expedition completion time is invalid")
        if observed < completed:
            raise ValueError("expedition completion precedes its observed time")
    elif observed >= started + EXPEDITION_DURATION_SECONDS:
        raise ValueError("elapsed expedition completion was not recorded")


def _validate_report(value, *, allow_legacy_shape=False):
    keys = set(value) if isinstance(value, dict) else set()
    legacy = allow_legacy_shape and keys == _LEGACY_REPORT_KEYS
    if not isinstance(value, dict) or keys != _REPORT_KEYS and not legacy:
        raise ValueError("expedition report has an invalid shape")
    _validate_uuid(value["report_id"], "report ID")
    _validate_outing_floor(value["outing_floor_id"])
    destination = _validate_floor(value["destination_floor_id"])
    category = value["category"]
    allowed_categories = ("training", "material") if legacy else ASSIGNMENT_CATEGORIES
    if category not in allowed_categories:
        raise ValueError("expedition report category is invalid")
    _validate_drifter_ids(value["expedition_drifter_ids"])
    started = _parse_utc(value["started_at_utc"])
    completed = _parse_utc(value["completed_at_utc"])
    if started is None or completed != started + EXPEDITION_DURATION_SECONDS:
        raise ValueError("expedition report timestamps are invalid")
    _nonnegative_int(value["secured_base_xp"], "secured expedition XP")
    awards = value["experience_awards"]
    if not isinstance(awards, dict):
        raise TypeError("expedition XP awards must be an object")
    if category == "training":
        ids = value["expedition_drifter_ids"]
        if set(awards) != set(ids):
            raise ValueError("training report must record both Drifter awards")
        for amount in awards.values():
            _nonnegative_int(amount, "expedition XP award")
        if value["reward_item_id"] is not None or value["reward_quantity"] != 0:
            raise ValueError("training report cannot contain a material reward")
    else:
        if awards:
            raise ValueError("non-training report cannot contain expedition XP")
        if category in {"material", "recovery", "elite"}:
            _positive_int(value["reward_quantity"], "expedition reward quantity")
        elif value["reward_item_id"] is not None or value["reward_quantity"] != 0:
            raise ValueError("non-item report cannot contain a stack reward")
    if not legacy:
        expected_content_id = report_content_id_for(destination, category)
        if value["report_content_id"] != expected_content_id:
            raise ValueError("expedition report content ID is invalid")
        _validate_frozen_outcome(category, destination, value["frozen_outcome"])
        expected_item, expected_quantity = _stack_reward(value["frozen_outcome"])
        if (
            value["reward_item_id"] != expected_item
            or value["reward_quantity"] != expected_quantity
        ):
            raise ValueError("expedition report reward disagrees with frozen outcome")
    if not isinstance(value["claimed"], bool):
        raise TypeError("expedition report claimed state must be a boolean")


def _validate_floor(value):
    if value not in FLOOR_IDS:
        raise ValueError("expedition floor is unknown")
    return value


def _validate_outing_floor(value):
    if value not in {
        "floor_one",
        "floor_two",
        "floor_four",
        FLOOR_FIVE_APPROACH_OUTING_ID,
    }:
        raise ValueError("expedition outing is not compatible with assignment")
    return value


def _validate_frozen_outcome(category, destination_floor_id, outcome):
    if category == "training":
        if outcome is not None:
            raise ValueError("training outcome is determined from secured outing XP")
        return
    if not isinstance(outcome, dict):
        raise ValueError("expedition outcome must be a frozen object")
    if category == "material":
        if destination_floor_id in FLOOR_IDS[:3]:
            expected_item = f"grade_{('i', 'ii', 'iii')[FLOOR_IDS.index(destination_floor_id)]}_metal"
            expected = {
                "source_id": None,
                "reward_item_id": expected_item,
                "reward_quantity": 1,
            }
        elif destination_floor_id == "floor_four":
            expected = {
                "source_id": "m8_floor_four_metal_drop_01",
                "reward_item_id": "grade_iv_metal",
                "reward_quantity": 1,
            }
            if not _has_authored_drop_source(
                "floor_four", expected["source_id"], expected["reward_item_id"]
            ):
                raise ValueError("Floor-IV Metal outcome has no authored source")
        else:
            source_id = outcome.get("source_id")
            if (
                source_id not in _floor_five_material_source_ids()
                or outcome.get("reward_item_id") != "grade_iv_cores"
                or outcome.get("reward_quantity") != 1
            ):
                raise ValueError("Floor-V Material outcome has no eligible source")
            return
        if outcome != expected:
            raise ValueError("Material outcome is not eligible for its destination")
        return
    if category == "equipment":
        if destination_floor_id != "floor_four" or set(outcome) != {
            "source_id", "equipment_instance"
        } or outcome["source_id"] != "m8_floor_four_armor_source":
            raise ValueError("equipment outcome is not eligible for this destination")
        from app.content.catalog import get_armor_reward_source
        from app.items.equipment import EquipmentInstance

        source = get_armor_reward_source(outcome["source_id"])
        instance = EquipmentInstance.from_snapshot(outcome["equipment_instance"])
        if (
            source.floor_id != destination_floor_id
            or instance.definition_id != source.template_id
            or instance.category != "armor"
            or instance.source_id != source.source_id
            or not instance.secured
        ):
            raise ValueError("equipment outcome disagrees with its authored source")
        return
    if category == "recovery":
        expected = {
            "source_id": "m8_floor_four_recovery_source",
            "reward_item_id": "healing_potion",
            "reward_quantity": 1,
        }
        if destination_floor_id != "floor_four" or outcome != expected:
            raise ValueError("Recovery outcome is not the authored Floor-IV item")
        from app.content.catalog import get_fixed_item_reward_source

        source = get_fixed_item_reward_source(outcome["source_id"])
        if source.floor_id != destination_floor_id:
            raise ValueError("Recovery outcome source belongs to another floor")
        return
    if category == "scouting":
        if (
            destination_floor_id != "floor_four"
            or outcome != {"knowledge_fact_ids": list(_SCOUTING_FACT_IDS)}
        ):
            raise ValueError("Scouting outcome does not match the approved facts")
        return
    if category == "story":
        if (
            destination_floor_id != "floor_four"
            or outcome != {"story_event_id": "m8_story_reliquary_echo"}
        ):
            raise ValueError("Story outcome is not the approved Floor-IV event")
        return
    if category == "elite":
        expected = {
            "source_id": "m8_floor_four_core_drop_01",
            "reward_item_id": "grade_iv_cores",
            "reward_quantity": 1,
        }
        if destination_floor_id != "floor_four" or outcome != expected:
            raise ValueError("Elite outcome is not the authored Floor-IV Core")
        if not _has_authored_drop_source(
            "floor_four", expected["source_id"], expected["reward_item_id"]
        ):
            raise ValueError("Floor-IV Core outcome has no authored source")
        return
    raise ValueError("expedition category has no frozen outcome contract")


def _stack_reward(outcome):
    if outcome is None or "reward_item_id" not in outcome:
        return None, 0
    return outcome["reward_item_id"], outcome["reward_quantity"]


def _has_authored_drop_source(floor_id, source_id, item_id):
    from app.content.catalog import get_encounter_spec, get_enemy_spec, get_route_spec

    try:
        route = get_route_spec(floor_id)
    except ValueError:
        return False
    for node in route.nodes:
        if node.encounter_id is None:
            continue
        encounter = get_encounter_spec(node.encounter_id)
        for archetype_id in encounter.enemy_archetype_ids:
            enemy = get_enemy_spec(archetype_id)
            for drop in enemy.item_drop_table_for_tier(3):
                if drop.source_id == source_id and drop.item_id == item_id:
                    return True
    return False


def _floor_five_material_source_ids():
    from app.content.catalog import get_encounter_spec, get_enemy_spec, get_route_spec

    source_ids = []
    for route_id in ("floor_five_approach", "floor_five_reunion"):
        try:
            route = get_route_spec(route_id)
        except ValueError:
            continue
        for node in route.nodes:
            if node.encounter_id is None:
                continue
            encounter = get_encounter_spec(node.encounter_id)
            for archetype_id in encounter.enemy_archetype_ids:
                enemy = get_enemy_spec(archetype_id)
                for tier in enemy.supported_tiers:
                    for drop in enemy.item_drop_table_for_tier(tier):
                        if drop.item_id == "grade_iv_cores" and drop.source_id:
                            if drop.source_id not in source_ids:
                                source_ids.append(drop.source_id)
    return tuple(source_ids)


def _validate_drifter_ids(value):
    if (
        not isinstance(value, list)
        or len(value) != 2
        or any(not isinstance(item, str) or not item for item in value)
        or len(value) != len(set(value))
    ):
        raise ValueError("expedition must record two distinct Drifter IDs")


def _validate_uuid(value, name):
    if not isinstance(value, str):
        raise TypeError(f"expedition {name} must be a canonical UUID")
    try:
        parsed = UUID(value)
    except (ValueError, TypeError, AttributeError) as error:
        raise ValueError(f"expedition {name} must be a canonical UUID") from error
    if str(parsed) != value:
        raise ValueError(f"expedition {name} must be a canonical UUID")


def _nonnegative_int(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")


def _positive_int(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")


def _utc_second(value):
    if isinstance(value, bool):
        raise ValueError("expedition time must be UTC seconds or an aware datetime")
    if isinstance(value, int):
        return value
    try:
        from datetime import datetime, timezone
    except ImportError as error:
        raise ValueError("expedition time must be UTC seconds on this runtime") from error
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ValueError("expedition time must be a timezone-aware datetime")
    try:
        utc_value = value.astimezone(timezone.utc)
        return _epoch_from_parts(
            utc_value.year,
            utc_value.month,
            utc_value.day,
            utc_value.hour,
            utc_value.minute,
            utc_value.second,
        )
    except (OverflowError, ValueError) as error:
        raise ValueError("expedition time is outside the supported range") from error


def _format_utc(value):
    parts = time.gmtime(_utc_second(value))
    return "%04d-%02d-%02dT%02d:%02d:%02dZ" % (
        parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
    )


def _parse_utc(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError("expedition UTC anchor must be a timestamp or null")
    if (
        len(value) != 20
        or value[4] != "-"
        or value[7] != "-"
        or value[10] != "T"
        or value[13] != ":"
        or value[16] != ":"
        or value[19] != "Z"
        or any(
            character < "0" or character > "9"
            for character in value[:4] + value[5:7] + value[8:10]
            + value[11:13] + value[14:16] + value[17:19]
        )
    ):
        raise ValueError("expedition UTC anchor must be canonical UTC")
    try:
        year = int(value[0:4])
        month = int(value[5:7])
        day = int(value[8:10])
        hour = int(value[11:13])
        minute = int(value[14:16])
        second = int(value[17:19])
        if year < 1 or not 1 <= month <= 12:
            raise ValueError("date is outside its valid range")
        month_lengths = (
            31, 29 if _is_leap_year(year) else 28, 31, 30, 31, 30,
            31, 31, 30, 31, 30, 31,
        )
        if not 1 <= day <= month_lengths[month - 1]:
            raise ValueError("day is outside its valid range")
        if not 0 <= hour <= 23 or not 0 <= minute <= 59 or not 0 <= second <= 59:
            raise ValueError("time is outside its valid range")
    except ValueError as error:
        raise ValueError("expedition UTC anchor must be canonical UTC") from error
    return _epoch_from_parts(year, month, day, hour, minute, second)


def _is_leap_year(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _epoch_from_parts(year, month, day, hour, minute, second):
    adjusted_year = year - (1 if month <= 2 else 0)
    era = adjusted_year // 400
    year_of_era = adjusted_year - era * 400
    shifted_month = month + (-3 if month > 2 else 9)
    day_of_year = (153 * shifted_month + 2) // 5 + day - 1
    day_of_era = (
        year_of_era * 365
        + year_of_era // 4
        - year_of_era // 100
        + day_of_year
    )
    days = era * 146097 + day_of_era - 719468
    return days * 86400 + hour * 3600 + minute * 60 + second


def _now_utc():
    return int(time.time())


__all__ = (
    "ASSIGNMENT_CATEGORIES",
    "EXPEDITION_DURATION_SECONDS",
    "EXPEDITION_LAUNCH_COST",
    "EXPEDITION_REGENERATION_SECONDS",
    "FLOOR_IDS",
    "MAX_EXPEDITION_ENERGY",
    "ExpeditionState",
    "category_unavailable_reason",
    "is_expeditions_unlocked",
)

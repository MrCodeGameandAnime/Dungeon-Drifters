"""Small portable expedition persistence and UTC-clock state."""

import time
from uuid import UUID

from app.snapshot import to_plain_value


MAX_EXPEDITION_ENERGY = 100
EXPEDITION_REGENERATION_SECONDS = 9 * 60
EXPEDITION_DURATION_SECONDS = 20 * 60
EXPEDITION_LAUNCH_COST = 10
FLOOR_IDS = ("floor_one", "floor_two", "floor_three")
ASSIGNMENT_CATEGORIES = ("training", "material")
_ASSIGNMENT_KEYS = {
    "assignment_id", "outing_floor_id", "destination_floor_id", "category",
    "expedition_drifter_ids", "started_at_utc", "last_observed_at_utc",
    "completed_at_utc",
}
_REPORT_KEYS = {
    "report_id", "outing_floor_id", "destination_floor_id", "category",
    "expedition_drifter_ids", "started_at_utc", "completed_at_utc",
    "secured_base_xp", "experience_awards", "reward_item_id",
    "reward_quantity", "claimed",
}


def is_expeditions_unlocked(game_state):
    return (
        game_state.party_state.tutorial_complete
        and game_state.party_state.floor_three_cleared
        and len(game_state.recruited_members) == 4
    )


def category_unavailable_reason(destination_floor_id, category):
    if destination_floor_id not in FLOOR_IDS:
        return "This destination has no authored M6 reward source."
    if category in ASSIGNMENT_CATEGORIES:
        return None
    if category == "equipment":
        return "No eligible authored equipment reward exists for this floor."
    if category == "recovery":
        return "No eligible authored recovery item exists for this floor."
    return "That expedition category is not available."


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
    def from_snapshot(cls, snapshot):
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
            _validate_assignment(assignment)
        reports = snapshot["reports"]
        if not isinstance(reports, list):
            raise TypeError("expedition reports must be a list")
        for report in reports:
            _validate_report(report)
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


def _validate_assignment(value):
    if not isinstance(value, dict) or set(value) != _ASSIGNMENT_KEYS:
        raise ValueError("active expedition assignment has an invalid shape")
    _validate_uuid(value["assignment_id"], "assignment ID")
    _validate_floor(value["outing_floor_id"])
    _validate_floor(value["destination_floor_id"])
    if value["outing_floor_id"] == "floor_three":
        raise ValueError("expeditions cannot accompany a Floor III outing")
    if value["category"] not in ASSIGNMENT_CATEGORIES:
        raise ValueError("expedition category is unavailable")
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


def _validate_report(value):
    if not isinstance(value, dict) or set(value) != _REPORT_KEYS:
        raise ValueError("expedition report has an invalid shape")
    _validate_uuid(value["report_id"], "report ID")
    _validate_floor(value["outing_floor_id"])
    destination = _validate_floor(value["destination_floor_id"])
    category = value["category"]
    if category not in ASSIGNMENT_CATEGORIES:
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
            raise ValueError("material report cannot contain expedition XP")
        expected = f"grade_{('i', 'ii', 'iii')[FLOOR_IDS.index(destination)]}_metal"
        if value["reward_item_id"] != expected or value["reward_quantity"] != 1:
            raise ValueError("material report reward is not floor-eligible")
    if not isinstance(value["claimed"], bool):
        raise TypeError("expedition report claimed state must be a boolean")


def _validate_floor(value):
    if value not in FLOOR_IDS:
        raise ValueError("expedition floor is unknown")
    return value


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

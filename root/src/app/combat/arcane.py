"""Shared rules and mechanical snapshots for Azhvielle's Arcane state."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GravemantleRules:
    overcharge_bonus_percent: int = 30
    break_mitigation_reduction_percent: int = 30
    backlash_chance_percent: int = 30
    backlash_damage_min: int = 6
    backlash_damage_max: int = 10
    instability_vulnerability_percent: int = 25


GRAVEMANTLE_RULES = GravemantleRules()


@dataclass(frozen=True)
class ArcaneDischarge:
    spell_bonus_percent: int
    broken_target: object | None
    break_reduction_percent: int
    instability_was_active: bool

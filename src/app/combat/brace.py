"""Shared rules for Branoc's Brace combat mechanic."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BraceRules:
    incoming_reduction_percent: int = 40
    follow_up_damage_bonus_percent: int = 30
    follow_up_mechanic: str = "heavy_attack"


BRACE_RULES = BraceRules()

"""Rules and authored markers for the generalized Frost mechanic."""

from dataclasses import dataclass


FROST_ATTACK_MECHANIC = "frost_attack"


@dataclass(frozen=True)
class FrostRules:
    frostbite_damage_per_tick: int = 5
    frostbite_duration_ticks: int = 3
    mournglass_backlash_chance_percent: int = 15


FROST_RULES = FrostRules()

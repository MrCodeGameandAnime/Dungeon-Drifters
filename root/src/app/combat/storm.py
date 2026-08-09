"""Shared mechanical rules for Joruun's storm sequence."""

from dataclasses import dataclass


HYDRO_WHIP_MECHANIC = "hydro_whip"
TEMPEST_SURGE_MECHANIC = "tempest_surge"
LIGHTNING_PALM_MECHANIC = "lightning_palm"


@dataclass(frozen=True)
class StormRules:
    conductive_damage_bonus_percent: int
    turbulence_damage_bonus_percent: int
    lightning_storm_damage_bonus_percent: int
    stun_chance_percent: int


STORM_RULES = StormRules(
    conductive_damage_bonus_percent=25,
    turbulence_damage_bonus_percent=35,
    lightning_storm_damage_bonus_percent=100,
    stun_chance_percent=35,
)

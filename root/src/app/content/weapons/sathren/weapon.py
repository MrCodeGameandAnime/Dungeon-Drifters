from app.content.weapon_spec import WeaponSpec
from app.content.weapon_progression_spec import (
    WeaponProgressionSpec,
    WeaponSlotSpec,
)


WEAPON = WeaponSpec(
    item_id="sathren",
    persistence_key="Sathren",
    name="Sathren",
    weapon_type="Alchemical Recurve Bow",
    intended_wielder="Zhaivra",
    stat_bonuses={"dexterity": 3, "intuition": 1},
    value=2,
    description=(
        "A recurved bow grown from the bone-fiber of the Hollow Colossus "
        "and fitted with six alchemical reservoirs."
    ),
    progression=WeaponProgressionSpec(
        slots=(
            WeaponSlotSpec(
                "grip_mechanism", "Grip / fittings / mechanism", "metal", "sathren_grip"
            ),
            WeaponSlotSpec("string", "String", "fiber", "sathren_string"),
            WeaponSlotSpec("limbs", "Limbs", "timber", "sathren_limbs"),
            WeaponSlotSpec(
                "reservoir_catalyst", "Reservoir / Catalyst", "cores", "sathren_reservoir"
            ),
        ),
    ),
)


__all__ = ["WEAPON"]

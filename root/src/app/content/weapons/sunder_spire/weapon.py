from app.content.weapon_spec import WeaponSpec
from app.content.weapon_progression_spec import (
    WeaponProgressionSpec,
    WeaponSlotSpec,
)


WEAPON = WeaponSpec(
    item_id="sunder_spire",
    persistence_key="SunderSpire",
    name="Sunder-Spire",
    weapon_type="Great Flamberge",
    intended_wielder="Branoc",
    stat_bonuses={"strength": 3, "constitution": 1},
    value=2,
    description="A massive Deep-Iron flamberge forged from the broken weapons of Rhom-Ghal.",
    progression=WeaponProgressionSpec(
        slots=(
            WeaponSlotSpec(
                "blade_guard", "Blade / Guard assembly", "metal", "sunder_spire_blade"
            ),
            WeaponSlotSpec(
                "grip_binding", "Grip wrap / binding", "fiber", "sunder_spire_grip"
            ),
            WeaponSlotSpec(
                "hilt_handle", "Hilt core / handle", "timber", "sunder_spire_hilt"
            ),
            WeaponSlotSpec(
                "crest_core", "Crest / Core", "cores", "sunder_spire_crest"
            ),
        ),
    ),
)


__all__ = ["WEAPON"]

from app.content.weapon_spec import WeaponSpec
from app.content.weapon_progression_spec import (
    WeaponProgressionSpec,
    WeaponSlotSpec,
)


WEAPON = WeaponSpec(
    item_id="sky_needle",
    persistence_key="SkyNeedle",
    name="Sky-Needle",
    weapon_type="Conductive Shakuj\u014d",
    intended_wielder="Joruun",
    stat_bonuses={"spirit": 2, "dexterity": 1, "intuition": 1},
    value=2,
    description=(
        "An ash-wood shakuj\u014d fitted with copper collars and loose "
        "conductive rings."
    ),
    progression=WeaponProgressionSpec(
        slots=(
            WeaponSlotSpec(
                "striking_head", "Head / Striking Cap", "metal", "sky_needle_head"
            ),
            WeaponSlotSpec(
                "binding_grip", "Binding / Grip", "fiber", "sky_needle_binding"
            ),
            WeaponSlotSpec("shaft", "Shaft", "timber", "sky_needle_shaft"),
            WeaponSlotSpec(
                "focus_collar", "Focus / Collar", "cores", "sky_needle_focus"
            ),
        ),
    ),
)


__all__ = ["WEAPON"]

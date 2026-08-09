from app.content.weapon_spec import WeaponSpec


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
)


__all__ = ["WEAPON"]

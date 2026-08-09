from app.content.weapon_spec import WeaponSpec


WEAPON = WeaponSpec(
    item_id="sunder_spire",
    persistence_key="SunderSpire",
    name="Sunder-Spire",
    weapon_type="Great Flamberge",
    intended_wielder="Branoc",
    stat_bonuses={"strength": 3, "constitution": 1},
    value=2,
    description="A massive Deep-Iron flamberge forged from the broken weapons of Rhom-Ghal.",
)


__all__ = ["WEAPON"]

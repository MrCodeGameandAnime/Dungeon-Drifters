from app.content.weapon_spec import WeaponSpec


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
)


__all__ = ["WEAPON"]

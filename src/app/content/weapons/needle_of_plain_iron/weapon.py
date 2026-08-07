from app.content.weapon_spec import WeaponSpec


WEAPON = WeaponSpec(
    item_id="needle_of_plain_iron",
    persistence_key="NeedleOfPlainIron",
    name="Needle of Plain Iron",
    weapon_type="Ritual Needle",
    intended_wielder="Azhvielle",
    stat_bonuses={"intelligence": 3, "spirit": 1},
    value=2,
    description=(
        "A long, unadorned iron needle used as both a weapon and a precise "
        "ritual focus."
    ),
)


__all__ = ["WEAPON"]

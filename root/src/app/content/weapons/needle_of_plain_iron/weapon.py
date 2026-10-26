from app.content.weapon_spec import WeaponSpec
from app.content.weapon_progression_spec import (
    WeaponProgressionSpec,
    WeaponSlotSpec,
)


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
    progression=WeaponProgressionSpec(
        slots=(
            WeaponSlotSpec(
                "focus_fittings", "Focus head / fittings", "metal", "needle_focus"
            ),
            WeaponSlotSpec("binding", "Binding", "fiber", "needle_binding"),
            WeaponSlotSpec("haft", "Haft", "timber", "needle_haft"),
            WeaponSlotSpec(
                "seal_catalyst", "Seal / Catalyst", "cores", "needle_seal"
            ),
        ),
    ),
)


__all__ = ["WEAPON"]

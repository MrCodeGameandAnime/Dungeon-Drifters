from app.content.weapon_spec import WeaponSpec
from app.content.weapon_progression_spec import (
    ComponentMoveModifierSpec,
    WeaponProgressionSpec,
    WeaponComponentSpec,
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
        components=(
            WeaponComponentSpec("needle_focus", "Unadorned Iron Focus Fittings", "focus_fittings", is_starting=True),
            WeaponComponentSpec("needle_binding", "Plain Binding", "binding", is_starting=True),
            WeaponComponentSpec("needle_haft", "Ritual Needle Haft", "haft", is_starting=True),
            WeaponComponentSpec("needle_seal", "Unawakened Seal", "seal_catalyst", is_starting=True),
            WeaponComponentSpec(
                "needle_focus_fitted", "Obsidian Focus Fittings", "focus_fittings",
                recipe_material_id="grade_i_metal", recipe_cost=1, crafting_award=10,
                physical_identity="Refined", physical_points=1,
                move_modifiers=(ComponentMoveModifierSpec("Scepter Sweep", 2, 0, -2),),
            ),
            WeaponComponentSpec(
                "needle_binding_warded", "Warded Binding", "binding",
                recipe_material_id="grade_i_fiber", recipe_cost=1, crafting_award=10,
                physical_identity="Refined", physical_points=1,
                move_modifiers=(ComponentMoveModifierSpec("Gloamweight Sepulcher", 0, -1, 0),),
            ),
            WeaponComponentSpec(
                "needle_haft_ashwood", "Ashwood Ritual Haft", "haft",
                recipe_material_id="grade_i_timber", recipe_cost=1, crafting_award=10,
                physical_identity="Refined", physical_points=1,
                move_modifiers=(ComponentMoveModifierSpec("Mournglass Bloom", 2, 0, -2),),
            ),
            WeaponComponentSpec(
                "needle_seal_faded", "Faded Seal Catalyst", "seal_catalyst",
                recipe_material_id="grade_i_cores", recipe_cost=1, crafting_award=10,
                mystical_identity="Mystic", mystical_points=2,
                move_modifiers=(ComponentMoveModifierSpec("Gravemantle Rupture", 2, 0, -2),),
            ),
        ),
    ),
)


__all__ = ["WEAPON"]

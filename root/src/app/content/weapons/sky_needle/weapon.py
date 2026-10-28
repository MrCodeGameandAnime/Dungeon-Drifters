from app.content.weapon_spec import WeaponSpec
from app.content.weapon_progression_spec import (
    ComponentMoveModifierSpec,
    WeaponProgressionSpec,
    WeaponComponentSpec,
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
        components=(
            WeaponComponentSpec("sky_needle_head", "Copper Striking Head", "striking_head", is_starting=True),
            WeaponComponentSpec("sky_needle_binding", "Conductive Ring Binding", "binding_grip", is_starting=True),
            WeaponComponentSpec("sky_needle_shaft", "Ash-Wood Shaft", "shaft", is_starting=True),
            WeaponComponentSpec("sky_needle_focus", "Loose Focus Collar", "focus_collar", is_starting=True),
            WeaponComponentSpec(
                "sky_needle_head_balanced", "Balanced Striking Head", "striking_head",
                recipe_material_id="grade_i_metal", recipe_cost=1, crafting_award=10,
                physical_identity="Refined", physical_points=1,
                move_modifiers=(ComponentMoveModifierSpec("Bring the Horse to Water", 2, 0, -2),),
            ),
            WeaponComponentSpec(
                "sky_needle_binding_conductive", "Conductive Grip Binding", "binding_grip",
                recipe_material_id="grade_i_fiber", recipe_cost=1, crafting_award=10,
                physical_identity="Refined", physical_points=1,
                move_modifiers=(ComponentMoveModifierSpec("Lightning Palm", 0, -1, 0),),
            ),
            WeaponComponentSpec(
                "sky_needle_shaft_flexible", "Flexible Ash-Wood Shaft", "shaft",
                recipe_material_id="grade_i_timber", recipe_cost=1, crafting_award=10,
                physical_identity="Refined", physical_points=1,
                move_modifiers=(ComponentMoveModifierSpec("Tempest Surge", 2, 0, -2),),
            ),
            WeaponComponentSpec(
                "sky_needle_focus_stormglass", "Stormglass Focus Collar", "focus_collar",
                recipe_material_id="grade_i_cores", recipe_cost=1, crafting_award=10,
                mystical_identity="Attuned", mystical_points=2,
                move_modifiers=(ComponentMoveModifierSpec("Coagulated Torrent", 2, 0, -2),),
            ),
        ),
    ),
)


__all__ = ["WEAPON"]

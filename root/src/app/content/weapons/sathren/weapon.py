from app.content.weapon_spec import WeaponSpec
from app.content.weapon_progression_spec import (
    ComponentMoveModifierSpec,
    WeaponProgressionSpec,
    WeaponComponentSpec,
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
                "grip_mechanism", "Grip / fittings / mechanism", "metal", "sathren_grip",
                governed_stats=("dexterity",),
            ),
            WeaponSlotSpec(
                "string", "String", "fiber", "sathren_string",
                governed_stats=("dexterity",),
            ),
            WeaponSlotSpec(
                "limbs", "Limbs", "timber", "sathren_limbs",
                governed_stats=("dexterity",),
            ),
            WeaponSlotSpec(
                "reservoir_catalyst", "Reservoir / Catalyst", "cores", "sathren_reservoir",
                governed_stats=("intuition",),
            ),
        ),
        components=(
            WeaponComponentSpec("sathren_grip", "Bone-Fiber Grip Mechanism", "grip_mechanism", is_starting=True),
            WeaponComponentSpec("sathren_string", "Recurved Bowstring", "string", is_starting=True),
            WeaponComponentSpec("sathren_limbs", "Hollow Colossus Limbs", "limbs", is_starting=True),
            WeaponComponentSpec("sathren_reservoir", "Six Alchemical Reservoirs", "reservoir_catalyst", is_starting=True),
            WeaponComponentSpec(
                "sathren_grip_precision", "Precision Grip Mechanism", "grip_mechanism",
                recipe_material_id="grade_i_metal", recipe_cost=1, crafting_award=10,
                physical_identity="Fast", physical_points=1,
                move_modifiers=(ComponentMoveModifierSpec("Mournpoint Verdict", 2, 0, -2),),
            ),
            WeaponComponentSpec(
                "sathren_string_taut", "Taut Recurve String", "string",
                recipe_material_id="grade_i_fiber", recipe_cost=1, crafting_award=10,
                physical_identity="Fast", physical_points=1,
                move_modifiers=(ComponentMoveModifierSpec("Hollowstring Trine", 2, 0, -2),),
            ),
            WeaponComponentSpec(
                "sathren_limbs_reinforced", "Reinforced Bow Limbs", "limbs",
                recipe_material_id="grade_i_timber", recipe_cost=1, crafting_award=10,
                physical_identity="Fast", physical_points=1,
                move_modifiers=(ComponentMoveModifierSpec("Nightskein Deluge", 2, 0, -2),),
            ),
            WeaponComponentSpec(
                "sathren_reservoir_alchemical", "Alchemical Reservoir Catalyst", "reservoir_catalyst",
                recipe_material_id="grade_i_cores", recipe_cost=1, crafting_award=10,
                mystical_identity="Attuned", mystical_points=2,
                move_modifiers=(ComponentMoveModifierSpec("Infused Barb", 2, 0, -2),),
            ),
        ),
    ),
)


__all__ = ["WEAPON"]

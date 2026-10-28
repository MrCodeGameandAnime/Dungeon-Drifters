from app.content.weapon_spec import WeaponSpec
from app.content.weapon_progression_spec import (
    ComponentMoveModifierSpec,
    WeaponProgressionSpec,
    WeaponComponentSpec,
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
        components=(
            WeaponComponentSpec("sunder_spire_blade", "Deep-Iron Blade and Guard", "blade_guard", is_starting=True),
            WeaponComponentSpec("sunder_spire_grip", "Bound Grip Wrap", "grip_binding", is_starting=True),
            WeaponComponentSpec("sunder_spire_hilt", "Ashwood Hilt Core", "hilt_handle", is_starting=True),
            WeaponComponentSpec("sunder_spire_crest", "Deep-Iron Crest", "crest_core", is_starting=True),
            WeaponComponentSpec(
                "sunder_spire_blade_reinforced", "Reinforced Blade and Guard", "blade_guard",
                recipe_material_id="grade_i_metal", recipe_cost=1, crafting_award=10,
                physical_identity="Heavy", physical_points=1,
                move_modifiers=(ComponentMoveModifierSpec("Crestgrave Reaping", 2, 0, -2),),
            ),
            WeaponComponentSpec(
                "sunder_spire_grip_braided", "Braided Grip Binding", "grip_binding",
                recipe_material_id="grade_i_fiber", recipe_cost=1, crafting_award=10,
                physical_identity="Heavy", physical_points=1,
                move_modifiers=(ComponentMoveModifierSpec("Cinderlung Vesper", 0, -1, 0),),
            ),
            WeaponComponentSpec(
                "sunder_spire_hilt_ashwood", "Reinforced Ashwood Hilt", "hilt_handle",
                recipe_material_id="grade_i_timber", recipe_cost=1, crafting_award=10,
                physical_identity="Heavy", physical_points=1,
                move_modifiers=(ComponentMoveModifierSpec("Ironwake Dismemberment", 2, 0, -2),),
            ),
            WeaponComponentSpec(
                "sunder_spire_crest_faded", "Faded Crest Core", "crest_core",
                recipe_material_id="grade_i_cores", recipe_cost=1, crafting_award=10,
                mystical_identity="Enchanted", mystical_points=2,
                move_modifiers=(ComponentMoveModifierSpec("Third Gate Obsequy", 2, 0, -2),),
            ),
        ),
    ),
)


__all__ = ["WEAPON"]

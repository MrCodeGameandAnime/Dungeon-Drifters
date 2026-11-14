"""Authored shared-item definitions and existing Alchemy recipes."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SupplyItemSpec:
    item_id: str
    display_name: str
    description: str
    base_price: int
    sellable: bool
    shop_stocked: bool = False
    carryable: bool = False
    healing_percent: int = 0
    mana_restore_percent: int = 0

    def __post_init__(self):
        for name in ("item_id", "display_name", "description"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be nonempty")
        if isinstance(self.base_price, bool) or not isinstance(self.base_price, int):
            raise TypeError("base_price must be an integer")
        if self.base_price < 0:
            raise ValueError("base_price must not be negative")
        for name in ("sellable", "shop_stocked", "carryable"):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be a boolean")
        if (
            isinstance(self.healing_percent, bool)
            or not isinstance(self.healing_percent, int)
            or not 0 <= self.healing_percent <= 100
        ):
            raise ValueError("healing_percent must be an integer from 0 to 100")
        if (
            isinstance(self.mana_restore_percent, bool)
            or not isinstance(self.mana_restore_percent, int)
            or not 0 <= self.mana_restore_percent <= 100
        ):
            raise ValueError("mana_restore_percent must be an integer from 0 to 100")


@dataclass(frozen=True)
class AlchemyRecipeSpec:
    recipe_id: str
    display_name: str
    ingredient_costs: tuple[tuple[str, int], ...]
    outputs: tuple[tuple[str, int], ...]

    def __post_init__(self):
        for name in ("recipe_id", "display_name"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be nonempty")
        for field_name in ("ingredient_costs", "outputs"):
            rows = getattr(self, field_name)
            if not isinstance(rows, tuple) or not rows:
                raise ValueError(f"{field_name} must be a nonempty tuple")
            item_ids = set()
            for item_id, quantity in rows:
                if not isinstance(item_id, str) or not item_id:
                    raise ValueError("recipe item IDs must be nonempty")
                if item_id in item_ids:
                    raise ValueError("recipe item IDs must be unique per side")
                if isinstance(quantity, bool) or not isinstance(quantity, int):
                    raise TypeError("recipe quantities must be integers")
                if quantity < 1:
                    raise ValueError("recipe quantities must be positive")
                item_ids.add(item_id)


SUPPLY_ITEMS = (
    SupplyItemSpec("goblin_scrap", "Goblin Scrap", "Useful salvage from goblins.", 3, True),
    SupplyItemSpec("goblin_lord_core", "Goblin Lord Core", "A rare core taken from the Floor I boss.", 0, False),
    SupplyItemSpec("grade_i_fiber", "Cord", "Grade-I fiber used for bindings and field craft.", 4, False, True),
    SupplyItemSpec("grade_i_cores", "Faded Core", "A faintly charged Grade-I core.", 4, False),
    SupplyItemSpec("medicinal_herb", "Medicinal Herb", "A common restorative plant.", 4, True, True),
    SupplyItemSpec("clean_water", "Clean Water", "Water suitable for alchemical preparations.", 4, True, True),
    SupplyItemSpec("charcoal_dust", "Charcoal Powder", "Fine charcoal used in alchemical preparations.", 4, True, True),
    SupplyItemSpec("smoke_powder", "Smoke Powder", "An intermediate alchemical mixture.", 0, False),
    SupplyItemSpec(
        "healing_potion",
        "Healing Potion",
        "Restores 40% of a Drifter's maximum HP.",
        12,
        False,
        True,
        True,
        healing_percent=40,
    ),
    SupplyItemSpec("smoke_bomb", "Smoke Bomb", "Ends a non-boss encounter without rewards.", 12, False, False, True),
    SupplyItemSpec("return_talisman", "Return Talisman", "Returns to the Hub with adjusted XP only.", 80, False, False, True),
    SupplyItemSpec("sulfur", "Sulfur", "A reactive alchemical ingredient.", 4, False),
    SupplyItemSpec("magic_reagent", "Magic Reagent", "A concentrated alchemical reagent.", 8, False),
    SupplyItemSpec("aether_dust", "Aether Dust", "Fine residue used in mana preparations.", 8, False),
    SupplyItemSpec(
        "mana_potion",
        "Mana Potion",
        "Restores 30% of a Drifter's maximum Mana.",
        20,
        False,
        carryable=True,
        mana_restore_percent=30,
    ),
    SupplyItemSpec("grade_i_magic_crystal", "Grade-I Magic Crystal", "A Grade-I crystal used for learned affixes.", 12, False),
    SupplyItemSpec("grade_ii_magic_crystal", "Grade-II Magic Crystal", "A Grade-II crystal used for learned affixes.", 24, False),
    SupplyItemSpec("grade_iii_magic_crystal", "Grade-III Magic Crystal", "A Grade-III crystal used for learned affixes.", 48, False),
    SupplyItemSpec("grade_iv_magic_crystal", "Grade-IV Magic Crystal", "A Grade-IV crystal reserved for later-floor content.", 96, False),
    SupplyItemSpec("mythril_plate", "Mythril Plate", "A rare smithing plate used in the Return Talisman recipe.", 80, False),
)

ALCHEMY_RECIPES = (
    AlchemyRecipeSpec(
        "healing_potion",
        "Healing Potion",
        (("medicinal_herb", 1), ("clean_water", 1)),
        (("healing_potion", 1),),
    ),
    AlchemyRecipeSpec(
        "smoke_powder",
        "Smoke Powder",
        (("goblin_scrap", 1), ("charcoal_dust", 1)),
        (("smoke_powder", 1),),
    ),
    AlchemyRecipeSpec(
        "smoke_bomb",
        "Smoke Bomb",
        (("smoke_powder", 1), ("grade_i_fiber", 1)),
        (("smoke_bomb", 1),),
    ),
    AlchemyRecipeSpec(
        "return_talisman",
        "Return Talisman",
        (("grade_i_cores", 1), ("grade_i_fiber", 1)),
        (("return_talisman", 1),),
    ),
)

_ITEMS_BY_ID = {item.item_id: item for item in SUPPLY_ITEMS}
_RECIPES_BY_ID = {recipe.recipe_id: recipe for recipe in ALCHEMY_RECIPES}


def get_supply_item(item_id):
    return _ITEMS_BY_ID.get(item_id)


def get_alchemy_recipe(recipe_id):
    return _RECIPES_BY_ID.get(recipe_id)

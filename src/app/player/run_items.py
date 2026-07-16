"""Authored definitions for character-owned run items and their uses."""

from dataclasses import dataclass
from enum import StrEnum

from app.player.character_run_state import (
    CINDERWRIT_PREPARATION_COST,
    InventoryActionId,
    RunItemId,
)


class InventoryCommand(StrEnum):
    INSPECT = "inspect"
    USE = "use"


@dataclass(frozen=True)
class RunItemDefinition:
    item_id: RunItemId
    display_name: str
    description: str
    commands: tuple[InventoryCommand, ...]

    def __post_init__(self):
        object.__setattr__(self, "item_id", RunItemId(self.item_id))
        for field_name in ("display_name", "description"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a nonempty string")
        if not isinstance(self.commands, tuple):
            raise TypeError("commands must be a tuple")
        object.__setattr__(
            self,
            "commands",
            tuple(InventoryCommand(command) for command in self.commands),
        )


@dataclass(frozen=True)
class InventoryRecipeDefinition:
    action_id: InventoryActionId
    ingredient_ids: tuple[RunItemId, ...]
    result_display_name: str

    def __post_init__(self):
        object.__setattr__(self, "action_id", InventoryActionId(self.action_id))
        if not isinstance(self.ingredient_ids, tuple):
            raise TypeError("ingredient_ids must be a tuple")
        ingredient_ids = tuple(RunItemId(item_id) for item_id in self.ingredient_ids)
        if len(ingredient_ids) < 2 or len(set(ingredient_ids)) != len(ingredient_ids):
            raise ValueError("recipes require at least two distinct ingredients")
        object.__setattr__(self, "ingredient_ids", ingredient_ids)
        if (
            not isinstance(self.result_display_name, str)
            or not self.result_display_name.strip()
        ):
            raise ValueError("result_display_name must be a nonempty string")


RUN_ITEM_DEFINITIONS = (
    RunItemDefinition(
        item_id=RunItemId.EMBER_SHARD,
        display_name="Ember Shard",
        description="A heat-bearing mineral used to empower weapons with fire.",
        commands=(InventoryCommand.INSPECT, InventoryCommand.USE),
    ),
    RunItemDefinition(
        item_id=RunItemId.DEEP_COAL,
        display_name="Deep Coal",
        description="A dense black catalyst used to bind heat into weapon runes.",
        commands=(InventoryCommand.INSPECT, InventoryCommand.USE),
    ),
)

CINDERWRIT_RECIPE = InventoryRecipeDefinition(
    action_id=InventoryActionId.PREPARE_CINDERWRIT,
    ingredient_ids=tuple(CINDERWRIT_PREPARATION_COST),
    result_display_name="Cinderwrit Barb",
)

INVENTORY_RECIPES = (CINDERWRIT_RECIPE,)


def run_item_definition(item_id):
    try:
        item_id = RunItemId(item_id)
    except (TypeError, ValueError):
        return None
    return next(
        (definition for definition in RUN_ITEM_DEFINITIONS if definition.item_id == item_id),
        None,
    )


def owned_run_item_definitions(character_run_state):
    return tuple(
        definition
        for definition in RUN_ITEM_DEFINITIONS
        if character_run_state.item_quantity(definition.item_id) > 0
    )


def inventory_recipe_for_pair(first_item_id, second_item_id):
    try:
        first_item_id = RunItemId(first_item_id)
        second_item_id = RunItemId(second_item_id)
    except (TypeError, ValueError):
        return None
    if first_item_id == second_item_id:
        return None
    return next(
        (
            recipe
            for recipe in INVENTORY_RECIPES
            if set(recipe.ingredient_ids) == {first_item_id, second_item_id}
        ),
        None,
    )


def owned_inventory_companions(character_run_state, source_item_id):
    try:
        source_item_id = RunItemId(source_item_id)
    except (TypeError, ValueError):
        return ()
    companion_ids = []
    for recipe in INVENTORY_RECIPES:
        if source_item_id not in recipe.ingredient_ids:
            continue
        companion_ids.extend(
            item_id
            for item_id in recipe.ingredient_ids
            if item_id != source_item_id
            and character_run_state.item_quantity(item_id) > 0
        )
    return tuple(
        definition
        for definition in RUN_ITEM_DEFINITIONS
        if definition.item_id in companion_ids
    )

"""Authoritative weapon-improvement and dismantling actions."""

from dataclasses import dataclass

import app.randomness as random
from app.iteration import first_or_none
from app.content.catalog import get_drifter_spec_by_choice, get_weapon_spec
from app.content.weapon_progression_spec import (
    QUALITY_GATES,
    get_dismantle_spec,
    get_improvement_recipe,
    improvement_roll,
    salvage_double_yield_chance,
    get_weapon_component_spec,
)
from app.game.party_state import DungeonPhase
from app.game.game_state import GameState
from app.player.player_state import PlayerState


@dataclass(frozen=True)
class WeaponProgressionResult:
    success: bool
    reason: str | None = None
    slot_progress: int | None = None
    roll: int | None = None
    material_id: str | None = None
    component_id: str | None = None
    slot_id: str | None = None
    crafting_level: int = 1
    _materials: tuple[tuple[str, int], ...] = ()

    @property
    def materials(self):
        return dict(self._materials)


class WeaponProgressionService:
    def __init__(self, game_state, *, rng=random):
        if not isinstance(game_state, GameState):
            raise TypeError("game_state must be a GameState")
        if not callable(getattr(rng, "randint", None)):
            raise TypeError("rng must provide randint")
        if not callable(getattr(rng, "choice", None)):
            raise TypeError("rng must provide choice")
        self._game_state = game_state
        self._rng = rng

    def improve_slot(self, *, target_drifter_id, slot_id):
        player = self._target_at_hub(target_drifter_id)
        state = player.signature_weapon_state
        weapon_spec = get_weapon_spec(state.weapon_id)
        slot = first_or_none(
            candidate
            for candidate in weapon_spec.progression.slots
            if candidate.slot_id == slot_id
        )
        if slot is None:
            raise ValueError(f"unknown signature weapon slot: {slot_id}")

        current = state.slot_progress[slot.slot_id]
        if current >= 100:
            return self._failure("maximum_progress", current)
        next_gate = next(gate for gate in QUALITY_GATES if current < gate)
        previous_gate = current // 25 * 25
        if previous_gate and not self._tier_is_unlocked(state, previous_gate):
            return self._failure("tier_locked", current)

        grade = min(4, current // 25 + 1)
        material_id = f"grade_{('i', 'ii', 'iii', 'iv')[grade - 1]}_{slot.material_family}"
        recipe = get_improvement_recipe(material_id)
        if self._game_state.party_state.shared_items.get(material_id, 0) < recipe.material_cost:
            return self._failure("insufficient_materials", current)

        roll = improvement_roll(
            self._game_state.party_state.crafting_level,
            self._rng,
        )
        new_progress = min(next_gate, current + roll)

        party = self._game_state.party_state
        if not party.spend_shared_items({material_id: recipe.material_cost}):
            return self._failure("insufficient_materials", current)
        state.set_slot_progress(slot.slot_id, new_progress)
        party.add_crafting_experience(recipe.crafting_award)
        return WeaponProgressionResult(
            success=True,
            slot_progress=new_progress,
            roll=roll,
            material_id=material_id,
            crafting_level=party.crafting_level,
        )

    def dismantle(self, *, target_drifter_id, item_id, quantity=1):
        self._target_at_hub(target_drifter_id)
        if isinstance(quantity, bool) or not isinstance(quantity, int):
            raise TypeError("quantity must be an integer")
        if quantity < 1:
            raise ValueError("quantity must be positive")
        spec = get_dismantle_spec(item_id)
        party = self._game_state.party_state
        if party.shared_items.get(item_id, 0) < quantity:
            return self._failure("insufficient_items")

        outputs = {}
        chance = salvage_double_yield_chance(party.crafting_level)
        for _ in range(quantity):
            material_id = self._rng.choice(spec.output_material_ids)
            yield_count = 1
            if spec.maximum_yield > 1 and self._rng.randint(1, 100) <= chance:
                yield_count = 2
            outputs[material_id] = outputs.get(material_id, 0) + yield_count

        if not party.spend_shared_items({item_id: quantity}):
            return self._failure("insufficient_items")
        party.add_shared_items(outputs)
        return WeaponProgressionResult(
            success=True,
            crafting_level=party.crafting_level,
            _materials=tuple(sorted(outputs.items())),
        )

    def craft_component(self, *, target_drifter_id, component_id):
        player = self._target_at_hub(target_drifter_id)
        progression = get_weapon_spec(
            player.signature_weapon_state.weapon_id
        ).progression
        try:
            component = get_weapon_component_spec(progression, component_id)
        except ValueError:
            return self._failure("unknown_component")
        if component.is_starting or component.recipe_material_id is None:
            return self._failure("not_craftable")

        party = self._game_state.party_state
        if party.shared_items.get(component.recipe_material_id, 0) < component.recipe_cost:
            return self._failure("insufficient_materials")
        if not party.spend_shared_items(
            {component.recipe_material_id: component.recipe_cost}
        ):
            return self._failure("insufficient_materials")
        party.add_shared_items({component.component_id: 1})
        party.add_crafting_experience(component.crafting_award)
        return WeaponProgressionResult(
            success=True,
            material_id=component.recipe_material_id,
            component_id=component.component_id,
            slot_id=component.slot_id,
            crafting_level=party.crafting_level,
        )

    def install_component(self, *, target_drifter_id, slot_id, component_id):
        player = self._target_at_hub(target_drifter_id)
        state = player.signature_weapon_state
        progression = get_weapon_spec(state.weapon_id).progression
        try:
            component = get_weapon_component_spec(progression, component_id)
        except ValueError:
            return self._failure("unknown_component")
        if component.slot_id != slot_id:
            return self._failure("wrong_slot")
        if state.components[slot_id] == component_id:
            return self._failure("already_installed")
        party = self._game_state.party_state
        if party.shared_items.get(component_id, 0) < 1:
            return self._failure("insufficient_components")
        if not party.spend_shared_items({component_id: 1}):
            return self._failure("insufficient_components")
        state.install_component(slot_id, component_id)
        return WeaponProgressionResult(
            success=True,
            component_id=component_id,
            slot_id=slot_id,
            crafting_level=party.crafting_level,
        )

    def _target_at_hub(self, target_drifter_id):
        if not isinstance(target_drifter_id, str) or not target_drifter_id:
            raise ValueError("target_drifter_id must identify a current party member")
        party = self._game_state.party_state
        if party.phase not in {DungeonPhase.HUB, DungeonPhase.PARTY_READY}:
            raise ValueError("weapon progression is only available at the Hub")
        members = (self._game_state.player_state,) + party.companions
        for member in members:
            profile = member.character.profile
            if profile is None:
                continue
            spec = get_drifter_spec_by_choice(profile.choice)
            if spec.drifter_id == target_drifter_id:
                return member
        raise ValueError("target Drifter is not in the current party")

    def _tier_is_unlocked(self, state, gate):
        return (
            all(progress >= gate for progress in state.slot_progress.values())
            and self._game_state.party_state.crafting_level >= gate
        )

    def _failure(self, reason, slot_progress=None):
        return WeaponProgressionResult(
            success=False,
            reason=reason,
            slot_progress=slot_progress,
            crafting_level=self._game_state.party_state.crafting_level,
        )


__all__ = ("WeaponProgressionResult", "WeaponProgressionService")

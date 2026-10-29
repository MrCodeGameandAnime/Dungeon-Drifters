"""Pure translation from persistent session state to overworld views."""

from app.content.catalog import (
    DRIFTER_SPECS,
    get_drifter_spec_by_choice,
    get_encounter_spec,
    get_enemy_spec,
    get_inspectable_route_node_spec,
    get_route_node_spec,
    get_route_spec,
    get_weapon_spec,
)
from app.content.weapon_progression_spec import (
    DISMANTLE_SPECS,
    MATERIAL_SPECS,
    TIER_V_ATTEMPT_SPEC,
    derive_weapon_identities,
    get_improvement_recipe,
    get_material_spec,
    get_weapon_component_spec,
)
from app.game.party_state import (
    COMPANION_RECRUITMENT_COST,
    DungeonPhase,
)
from app.content.route_spec import RouteNodeKind
from app.game.game_state import GameState
from app.game.overworld_state import ContextualRoutePhase
from app.iteration import first_or_none
from app.items.weapon import Weapon
from app.player.run_items import owned_run_item_definitions
from app.presentation.overworld_models import (
    AccessorySlotView,
    CharacterOverviewView,
    CompanionChoiceView,
    EquipmentView,
    InventoryView,
    MapNodeState,
    MapNodeView,
    MapView,
    MapEncounterInspectionView,
    MerchantDismantleView,
    MerchantComponentRecipeView,
    MerchantMaterialView,
    MerchantSlotView,
    MerchantTierVMaterialView,
    MerchantTierVView,
    MerchantTargetView,
    MerchantView,
    OverworldAction,
    OverworldAvailabilityReason,
    OverworldItemView,
    OverworldOptionView,
    OutingItemRewardView,
    OutingRewardsView,
    OverworldScreen,
    OverworldView,
    SkillMoveView,
    SkillsView,
    StatBonusView,
    StatRowView,
    WeaponView,
    WeaponComponentSlotView,
)


STAT_ORDER = (
    ("strength", "Strength"),
    ("constitution", "Constitution"),
    ("intelligence", "Intelligence"),
    ("spirit", "Spirit"),
    ("dexterity", "Dexterity"),
    ("intuition", "Intuition"),
)

_SURFACE_ROUTE = get_route_spec("surface")
_FIRST_SURFACE_NODE_ID = _SURFACE_ROUTE.nodes[0].node_id


def _adjacent_run_counts(values):
    groups = []
    for value in values:
        if groups and groups[-1][0] == value:
            previous_value, count = groups[-1]
            groups[-1] = (previous_value, count + 1)
        else:
            groups.append((value, 1))
    return tuple(groups)


def _member_drifter_spec(member):
    profile = member.character.profile
    if profile is not None:
        return get_drifter_spec_by_choice(profile.choice)
    weapon = member.get_equipped("weapon")
    weapon_id = weapon.item_id if isinstance(weapon, Weapon) else None
    return next(
        spec
        for spec in DRIFTER_SPECS
        if spec.starting_weapon_id == weapon_id
    )


class OverworldPresenter:
    def build(
        self,
        game_state,
        *,
        screen=OverworldScreen.MAIN,
        selected_item_key=None,
        selected_character_target_id=None,
        selected_merchant_target_id=None,
        selected_weapon_target_id=None,
        adventure_text=None,
        notice=None,
        save_available=False,
        load_available=False,
    ):
        if not isinstance(game_state, GameState):
            raise TypeError("game_state must be a GameState")
        screen = OverworldScreen(screen)
        node = get_route_node_spec(game_state.overworld_state.current_route_node_id)
        if adventure_text is None:
            adventure_text = (
                self._hub_adventure_text(game_state, screen)
                if screen
                in {
                    OverworldScreen.HUB,
                    OverworldScreen.FLOOR_ONE_WARNING,
                    OverworldScreen.COMPANION_SELECTION,
                    OverworldScreen.PARTY_READY,
                    OverworldScreen.OUTING,
                    OverworldScreen.EXTRACTION,
                    OverworldScreen.MERCHANT,
                }
                else self._default_adventure_text(game_state)
            )
        items = self._inventory_items(game_state)
        selected_item = first_or_none(
            item
            for item in items
            if item.selection_key == selected_item_key
        )
        options = self._options(
            game_state,
            screen,
            selected_item,
            save_available=save_available,
            load_available=load_available,
        )
        contextual_route_option = self._contextual_route_option(
            game_state,
            screen,
        )

        return OverworldView(
            screen=screen,
            location_label=(
                node.display_label
                if game_state.overworld_state.active_route_id == "floor_one"
                and game_state.party_state.phase
                in {DungeonPhase.OUTING, DungeonPhase.EXTRACTION}
                else (
                    "Floor 1 Hub"
                    if game_state.party_state.phase is not DungeonPhase.OUTSIDE
                    else node.display_label
                )
            ),
            adventure_text=adventure_text,
            notice=notice,
            options=options,
            contextual_route_option=contextual_route_option,
            character=(
                self._character_view(game_state, selected_character_target_id)
                if screen is OverworldScreen.CHARACTER
                else None
            ),
            skills=(
                self._skills_view(game_state, selected_character_target_id)
                if screen is OverworldScreen.SKILLS
                else None
            ),
            weapon=(
                self._weapon_view(game_state, selected_weapon_target_id)
                if screen is OverworldScreen.WEAPON
                else None
            ),
            merchant=(
                self._merchant_view(game_state, selected_merchant_target_id)
                if screen is OverworldScreen.MERCHANT
                else None
            ),
            equipment=(
                self._equipment_view(game_state, selected_character_target_id)
                if screen is OverworldScreen.EQUIPMENT
                else None
            ),
            inventory=(
                InventoryView(
                    items=items,
                    selected_item_key=(
                        selected_item.selection_key if selected_item else None
                    ),
                    inspected_item=(
                        selected_item
                        if screen is OverworldScreen.ITEM_INSPECT
                        else None
                    ),
                )
                if screen in {OverworldScreen.ITEMS, OverworldScreen.ITEM_INSPECT}
                else None
            ),
            route_map=(
                self._map_view(game_state)
                if screen is OverworldScreen.MAP
                else None
            ),
            encounter_inspection=(
                self._map_encounter_inspection_view(game_state)
                if screen is OverworldScreen.MAP_INSPECT
                else None
            ),
            companion_choices=(
                self._companion_choices(game_state)
                if screen is OverworldScreen.COMPANION_SELECTION
                else ()
            ),
            shared_gold=(
                game_state.party_state.shared_gold
                if screen
                in {
                    OverworldScreen.HUB,
                    OverworldScreen.COMPANION_SELECTION,
                    OverworldScreen.PARTY_READY,
                }
                else None
            ),
            recruitment_cost=(
                COMPANION_RECRUITMENT_COST
                if screen is OverworldScreen.COMPANION_SELECTION
                else None
            ),
            outing_rewards=(
                OutingRewardsView(
                    experience=game_state.party_state.outing_rewards.experience,
                    gold=game_state.party_state.outing_rewards.gold,
                    items=tuple(
                        OutingItemRewardView(
                            item_id=item_id,
                            quantity=quantity,
                            display_name=self._shared_item_display_name(item_id),
                        )
                        for item_id, quantity in sorted(
                            game_state.party_state.outing_rewards.items.items()
                        )
                    ),
                )
                if screen is OverworldScreen.EXTRACTION
                else None
            ),
        )

    @staticmethod
    def _hub_adventure_text(game_state, screen):
        if screen is OverworldScreen.COMPANION_SELECTION:
            return "Choose one Drifter to join your party."
        if screen is OverworldScreen.FLOOR_ONE_WARNING:
            return (
                "Death means returning to the Hub. All unsecured XP, gold, "
                "and items are lost. No retry, rewind, or continue."
            )
        if screen is OverworldScreen.PARTY_READY:
            return "Your party is ready to set out."
        if screen is OverworldScreen.OUTING:
            return "Your party has set out from the Floor 1 Hub."
        if screen is OverworldScreen.EXTRACTION:
            return "The Goblin trio is defeated. Return to the hub to secure your rewards."
        if screen is OverworldScreen.MERCHANT:
            return "Improve a party Drifter's signature weapon with shared supplies."
        if game_state.party_state.phase is DungeonPhase.PARTY_READY:
            return "Your party is assembled and ready to set out."
        if game_state.party_state.tutorial_complete:
            return "Your party has returned to the Floor 1 Hub. Prepare for the next outing."
        return "You have reached the Floor 1 Hub. Recruit one companion to continue."

    @staticmethod
    def _companion_choices(game_state):
        profile = game_state.player_state.character.profile
        if profile is None:
            raise ValueError("companion selection requires a canonical lead Drifter")
        lead_id = profile.drifter_id
        shared_gold = game_state.party_state.shared_gold
        enabled = shared_gold >= COMPANION_RECRUITMENT_COST
        return tuple(
            CompanionChoiceView(
                drifter_id=spec.drifter_id,
                display_name=spec.display_name,
                archetype_label=spec.archetype_name,
                summary=spec.selection_summary,
                cost=COMPANION_RECRUITMENT_COST,
                enabled=enabled,
                disabled_reason=(
                    None
                    if enabled
                    else OverworldAvailabilityReason.INSUFFICIENT_SHARED_GOLD
                ),
            )
            for spec in DRIFTER_SPECS
            if spec.drifter_id != lead_id
        )

    @staticmethod
    def _default_adventure_text(game_state):
        current_label = get_route_node_spec(
            game_state.overworld_state.current_route_node_id
        ).display_label
        phase = game_state.overworld_state.current_contextual_route_phase
        if phase is ContextualRoutePhase.RETRY:
            return f"{current_label} still blocks the route. Regroup and try again."
        if phase is ContextualRoutePhase.NONE:
            return f"{current_label} is cleared. The route continues ahead."
        if (
            game_state.overworld_state.current_route_node_id
            == _FIRST_SURFACE_NODE_ID
        ):
            return "The road through Ketlyv begins at the edge of the Goblin horde."
        return f"{current_label} awaits along the surface route."

    def _character_view(self, game_state, selected_target_id):
        player, selected_target_id, targets = self._selected_party_member(
            game_state,
            selected_target_id,
        )
        level = player.level_state
        exp = player.exp_state
        threshold = level.next_threshold
        fill_bps = (
            10_000
            if threshold is None
            else min(10_000, exp.current * 10_000 // threshold)
        )
        return CharacterOverviewView(
            display_name=player.character.full_display_name,
            archetype_label=player.character.archetype_name,
            stats=self._stats(player),
            level=level.current,
            exp_current=exp.current,
            exp_threshold=threshold,
            exp_fill_bps=fill_bps,
            hp_current=player.health.current,
            hp_maximum=player.health.maximum,
            mana_current=player.mana_resource.current,
            mana_maximum=player.mana_resource.maximum,
            super_current=player.super_resource.current,
            super_maximum=player.super_resource.maximum,
            targets=targets,
            selected_target_id=selected_target_id,
        )

    def _skills_view(self, game_state, selected_target_id):
        player, selected_target_id, targets = self._selected_party_member(
            game_state,
            selected_target_id,
        )
        growth_points = player.growth_points
        return SkillsView(
            growth_points_available=growth_points,
            growth_message=(
                "Spend 1 Growth Point to increase one permanent stat by 1."
                if growth_points
                else "Earn Growth Points by leveling up."
            ),
            stats=self._stats(player, increase_controls=True),
            moves=tuple(
                SkillMoveView(
                    name=move.name,
                    description=move.description,
                    power=move.power,
                    accuracy=move.accuracy,
                    resource_type=move.resource_type.value,
                    resource_cost=move.resource_cost,
                    damage_type=move.damage_type.value,
                )
                for move in player.combat_moves
            ),
            targets=targets,
            selected_target_id=selected_target_id,
        )

    @staticmethod
    def _selected_party_member(game_state, selected_target_id):
        members = (game_state.player_state,) + game_state.party_state.companions
        member_specs = tuple((member, _member_drifter_spec(member)) for member in members)
        target_ids = {spec.drifter_id for _member, spec in member_specs}
        if selected_target_id not in target_ids:
            selected_target_id = member_specs[0][1].drifter_id
        targets = tuple(
            MerchantTargetView(
                drifter_id=spec.drifter_id,
                display_name=member.character.full_display_name,
                selected=spec.drifter_id == selected_target_id,
            )
            for member, spec in member_specs
        )
        member = next(
            member
            for member, spec in member_specs
            if spec.drifter_id == selected_target_id
        )
        return member, selected_target_id, targets

    @staticmethod
    def _stats(player, *, increase_controls=False):
        values = player.character.permanent_stats.as_dict()
        return tuple(
            StatRowView(
                stat_name=name,
                label=label,
                value=values[name],
                increase_visible=increase_controls,
                increase_enabled=(
                    increase_controls
                    and values[name] < player.character.permanent_stats.MAXIMUM
                    and player.growth_points > 0
                ),
                disabled_reason=(
                    None
                    if not increase_controls
                    or (
                        values[name] < player.character.permanent_stats.MAXIMUM
                        and player.growth_points > 0
                    )
                    else (
                        OverworldAvailabilityReason.STAT_AT_MAXIMUM
                        if values[name] >= player.character.permanent_stats.MAXIMUM
                        else OverworldAvailabilityReason.NO_GROWTH_POINTS
                    )
                ),
            )
            for name, label in STAT_ORDER
        )

    @staticmethod
    def _weapon_view(game_state, selected_target_id):
        members = (game_state.player_state,) + game_state.party_state.companions
        target_specs = tuple(
            (member, _member_drifter_spec(member))
            for member in members
        )
        target_ids = {spec.drifter_id for _member, spec in target_specs}
        if selected_target_id not in target_ids:
            selected_target_id = target_specs[0][1].drifter_id
        target_member = next(
            member
            for member, spec in target_specs
            if spec.drifter_id == selected_target_id
        )
        weapon = target_member.get_equipped("weapon")
        if not isinstance(weapon, Weapon):
            raise ValueError("the selected Drifter has no equipped signature weapon")
        weapon_spec = get_weapon_spec(weapon.item_id)
        progression = weapon_spec.progression
        component_state = target_member.signature_weapon_state
        bonuses = tuple(
            StatBonusView(label, weapon.stat_bonuses[name])
            for name, label in STAT_ORDER
            if name in weapon.stat_bonuses
        )
        targets = tuple(
            MerchantTargetView(
                drifter_id=spec.drifter_id,
                display_name=member.character.full_display_name,
                selected=spec.drifter_id == selected_target_id,
            )
            for member, spec in target_specs
        )
        component_slots = []
        for slot in progression.slots:
            installed_id = component_state.components[slot.slot_id]
            installed = get_weapon_component_spec(progression, installed_id)
            component_slots.append(
                WeaponComponentSlotView(
                    slot_id=slot.slot_id,
                    label=slot.label,
                    installed_component_id=installed_id,
                    installed_component_name=installed.display_name,
                    installed_effect_summary=OverworldPresenter._component_effect_summary(installed),
                )
            )
        physical_identity, mystical_identity = derive_weapon_identities(
            progression,
            component_state.components,
        )
        return WeaponView(
            name=weapon.name,
            weapon_type=weapon.weapon_type,
            intended_wielder=weapon.intended_wielder,
            bonuses=bonuses,
            description=weapon.description,
            targets=targets,
            selected_target_id=selected_target_id,
            components=tuple(component_slots),
            physical_identity=physical_identity,
            mystical_identity=mystical_identity,
        )

    @staticmethod
    def _merchant_view(game_state, selected_target_id):
        party = game_state.party_state
        members = (game_state.player_state,) + party.companions
        target_specs = tuple(
            (
                member,
                _member_drifter_spec(member),
            )
            for member in members
        )
        target_ids = {spec.drifter_id for _member, spec in target_specs}
        if selected_target_id not in target_ids:
            selected_target_id = target_specs[0][1].drifter_id
        target_member = next(
            member
            for member, spec in target_specs
            if spec.drifter_id == selected_target_id
        )
        weapon_state = target_member.signature_weapon_state
        weapon_spec = get_weapon_spec(weapon_state.weapon_id)
        target_views = tuple(
            MerchantTargetView(
                drifter_id=spec.drifter_id,
                display_name=member.character.full_display_name,
                selected=spec.drifter_id == selected_target_id,
            )
            for member, spec in target_specs
        )

        slots = []
        for slot in weapon_spec.progression.slots:
            current = weapon_state.slot_progress[slot.slot_id]
            grade = min(4, current // 25 + 1)
            material_id = f"grade_{('i', 'ii', 'iii', 'iv')[grade - 1]}_{slot.material_family}"
            recipe = get_improvement_recipe(material_id)
            quantity = party.shared_items.get(material_id, 0)
            gate = current // 25 * 25
            tier_locked = bool(
                gate
                and (
                    not all(
                        value >= gate
                        for value in weapon_state.slot_progress.values()
                    )
                    or party.crafting_level < gate
                )
            )
            blocked_reason = (
                "maximum_progress"
                if current >= 100
                else (
                    "tier_locked"
                    if tier_locked
                    else "insufficient_materials"
                    if quantity < recipe.material_cost
                    else None
                )
            )
            slots.append(
                MerchantSlotView(
                    slot_id=slot.slot_id,
                    label=slot.label,
                    material_family=slot.material_family,
                    progress=current,
                    material_id=material_id,
                    material_name=get_material_spec(material_id).display_name,
                    material_cost=recipe.material_cost,
                    material_quantity=quantity,
                    can_improve=blocked_reason is None,
                    blocked_reason=blocked_reason,
                )
            )

        stock_by_id = dict(party.shared_items)
        material_ids = {
            spec.item_id for spec in MATERIAL_SPECS if spec.grade == 1
        }
        known_material_ids = {spec.item_id for spec in MATERIAL_SPECS}
        material_ids.update(
            item_id for item_id in stock_by_id if item_id in known_material_ids
        )
        materials = tuple(
            MerchantMaterialView(
                item_id=item_id,
                display_name=get_material_spec(item_id).display_name,
                quantity=stock_by_id.get(item_id, 0),
            )
            for item_id in sorted(material_ids)
        )
        dismantle_items = tuple(
            MerchantDismantleView(
                item_id=spec.item_id,
                display_name=spec.item_id.replace("_", " ").title(),
                quantity=stock_by_id[spec.item_id],
                output_material_names=tuple(
                    get_material_spec(item_id).display_name
                    for item_id in spec.output_material_ids
                ),
                maximum_yield=spec.maximum_yield,
            )
            for spec in DISMANTLE_SPECS
            if stock_by_id.get(spec.item_id, 0) > 0
        )
        component_recipes = tuple(
            MerchantComponentRecipeView(
                component_id=component.component_id,
                display_name=component.display_name,
                slot_id=component.slot_id,
                slot_label=next(
                    slot.label
                    for slot in weapon_spec.progression.slots
                    if slot.slot_id == component.slot_id
                ),
                material_name=get_material_spec(component.recipe_material_id).display_name,
                material_cost=component.recipe_cost,
                material_quantity=stock_by_id.get(component.recipe_material_id, 0),
                crafting_award=component.crafting_award,
                can_craft=(
                    stock_by_id.get(component.recipe_material_id, 0)
                    >= component.recipe_cost
                ),
                effect_summary=OverworldPresenter._component_effect_summary(component),
            )
            for component in weapon_spec.progression.components
            if not component.is_starting
            and weapon_state.components[component.slot_id] != component.component_id
        )
        tier_v_materials = tuple(
            MerchantTierVMaterialView(
                item_id=material_id,
                display_name=get_material_spec(material_id).display_name,
                required=quantity,
                available=stock_by_id.get(material_id, 0),
            )
            for material_id, quantity in TIER_V_ATTEMPT_SPEC.material_costs
        )
        tier_v_completed = weapon_state.tier_v_success
        tier_v_locked = (
            any(value < 100 for value in weapon_state.slot_progress.values())
            or party.crafting_level < 100
        )
        tier_v_materials_missing = any(
            material.available < material.required
            for material in tier_v_materials
        )
        tier_v_blocked_reason = (
            None
            if tier_v_completed
            else "tier_locked"
            if tier_v_locked
            else "insufficient_materials"
            if tier_v_materials_missing
            else None
        )
        tier_v = MerchantTierVView(
            success_chance_percent=TIER_V_ATTEMPT_SPEC.success_chance_percent,
            materials=tier_v_materials,
            can_attempt=(
                not tier_v_completed and tier_v_blocked_reason is None
            ),
            completed=tier_v_completed,
            blocked_reason=tier_v_blocked_reason,
        )
        return MerchantView(
            crafting_level=party.crafting_level,
            crafting_experience=party.crafting_experience,
            targets=target_views,
            selected_target_id=selected_target_id,
            weapon_name=weapon_spec.name,
            slots=tuple(slots),
            materials=materials,
            dismantle_items=dismantle_items,
            component_recipes=component_recipes,
            tier_v=tier_v,
        )

    @staticmethod
    def _component_effect_summary(component):
        effects = []
        for modifier in component.move_modifiers:
            changes = []
            if modifier.power_delta:
                changes.append(f"Power {modifier.power_delta:+d}")
            if modifier.accuracy_delta:
                changes.append(f"Accuracy {modifier.accuracy_delta:+d}")
            if modifier.resource_cost_delta:
                changes.append(f"Resource cost {modifier.resource_cost_delta:+d}")
            if modifier.damage_type is not None:
                changes.append(f"Damage type {modifier.damage_type.title()}")
            effects.append(f"{modifier.move_name}: {', '.join(changes)}")
        if component.physical_identity is not None:
            effects.append(
                f"{component.physical_identity} identity +{component.physical_points}"
            )
        if component.mystical_identity is not None:
            effects.append(
                f"{component.mystical_identity} identity +{component.mystical_points}"
            )
        return tuple(effects)

    @staticmethod
    def _equipment_view(game_state, selected_target_id):
        _member, selected_target_id, targets = OverworldPresenter._selected_party_member(
            game_state,
            selected_target_id,
        )
        return EquipmentView(
            necklace=AccessorySlotView("Necklace", "Empty"),
            ring=AccessorySlotView("Ring", "Empty"),
            benefits=("None",),
            targets=targets,
            selected_target_id=selected_target_id,
        )

    @staticmethod
    def _shared_item_display_name(item_id):
        try:
            return get_material_spec(item_id).display_name
        except ValueError:
            pass
        for drifter in DRIFTER_SPECS:
            progression = get_weapon_spec(drifter.starting_weapon_id).progression
            for component in progression.components:
                if component.component_id == item_id:
                    return component.display_name
        return " ".join(
            part[:1].upper() + part[1:]
            for part in item_id.split("_")
        )

    @staticmethod
    def _inventory_items(game_state):
        player = game_state.player_state
        items = []
        for index, item in enumerate(player.inventory.items, start=1):
            if isinstance(item, Weapon):
                items.append(
                    OverworldItemView(
                        selection_key=f"owned-item-{index}",
                        display_name=item.name,
                        quantity=1,
                        description=item.description,
                    )
                )
        for definition in owned_run_item_definitions(player.character_run_state):
            items.append(
                OverworldItemView(
                    selection_key=f"run-item:{definition.item_id.value}",
                    display_name=definition.display_name,
                    quantity=player.character_run_state.item_quantity(
                        definition.item_id
                    ),
                    description=definition.description,
                )
            )
        shared_items = game_state.party_state.shared_items
        for item_id, quantity in sorted(
            shared_items.items(),
            key=lambda item: OverworldPresenter._shared_item_display_name(item[0]),
        ):
            items.append(
                OverworldItemView(
                    selection_key=f"shared-item:{item_id}",
                    display_name=OverworldPresenter._shared_item_display_name(item_id),
                    quantity=quantity,
                    description="Shared crafting material or weapon component.",
                )
            )
        return tuple(items)

    @staticmethod
    def _map_view(game_state):
        overworld = game_state.overworld_state
        current_id = overworld.current_route_node_id
        route = get_route_spec(overworld.active_route_id)
        route_nodes = route.nodes
        defeated_encounters = set(game_state.world_state.defeated_encounters)
        resolved_rest_nodes = set(
            overworld.resolved_rest_node_ids
        )
        floor_one_cursor = (
            tuple(node.node_id for node in route_nodes).index(current_id)
            if overworld.active_route_id == "floor_one"
            else None
        )
        floor_one_node_indexes = (
            {node.node_id: index for index, node in enumerate(route_nodes)}
            if floor_one_cursor is not None
            else None
        )

        def is_completed(node):
            if node.kind in {RouteNodeKind.COMBAT, RouteNodeKind.BOSS}:
                return node.encounter_id in defeated_encounters
            if node.kind is RouteNodeKind.REST:
                return node.node_id in resolved_rest_nodes
            return False

        return MapView(
            nodes=tuple(
                MapNodeView(
                    display_label=node.display_label,
                    kind_label={
                        RouteNodeKind.COMBAT: "Encounter",
                        RouteNodeKind.REST: "Rest",
                        RouteNodeKind.BOSS: "Boss",
                        RouteNodeKind.DUNGEON_ENTRANCE: "Dungeon",
                    }[node.kind],
                    state=(
                        MapNodeState.CURRENT
                        if node.node_id == current_id
                        else (
                            MapNodeState.COMPLETED
                            if (
                                floor_one_node_indexes[node.node_id]
                                < floor_one_cursor
                                if floor_one_cursor is not None
                                else is_completed(node)
                            )
                            else MapNodeState.REMAINING
                        )
                    ),
                )
                for node in route_nodes
            )
        )

    @staticmethod
    def _map_encounter_inspection_view(game_state):
        inspection_node = get_inspectable_route_node_spec(
            game_state.overworld_state.current_route_node_id
        )
        if inspection_node is None:
            return None
        encounter = get_encounter_spec(inspection_node.encounter_id)

        composition = []
        for archetype_id, count in _adjacent_run_counts(
            encounter.enemy_archetype_ids
        ):
            enemy_spec = get_enemy_spec(archetype_id)
            composition.append(
                enemy_spec.name
                if count == 1
                else f"{count} {enemy_spec.name}s"
            )

        return MapEncounterInspectionView(
            encounter_label=inspection_node.display_label,
            composition=tuple(composition),
            boss=inspection_node.kind is RouteNodeKind.BOSS,
        )

    def _options(
        self,
        game_state,
        screen,
        selected_item,
        *,
        save_available=False,
        load_available=False,
    ):
        enabled = self._enabled_option
        disabled = self._disabled_option
        if screen is OverworldScreen.MAIN:
            return (
                enabled(OverworldAction.CHARACTER, "Character"),
                enabled(OverworldAction.ITEMS, "Items"),
                enabled(OverworldAction.MAP, "Map"),
                enabled(OverworldAction.OPTIONS, "Options"),
            )
        if screen is OverworldScreen.HUB:
            party_state = game_state.party_state
            merchant_action = ()
            if party_state.phase is DungeonPhase.HUB:
                merchant_action = (enabled(OverworldAction.MERCHANT, "Merchant"),)
                party_actions = (
                    (
                        enabled(OverworldAction.START_FLOOR_ONE, "Start Floor 1"),
                    )
                    if party_state.tutorial_complete
                    else (
                        enabled(
                            OverworldAction.RECRUIT_COMPANION,
                            "Recruit Companion",
                        ),
                    )
                )
            elif party_state.phase is DungeonPhase.PARTY_READY:
                party_actions = (
                    enabled(OverworldAction.READY, "Ready / Set Out"),
                )
            else:
                party_actions = ()
            return merchant_action + party_actions + (
                enabled(OverworldAction.CHARACTER, "Character"),
                enabled(OverworldAction.ITEMS, "Items"),
                enabled(OverworldAction.MAP, "Map"),
                enabled(OverworldAction.OPTIONS, "Options"),
            )
        if screen is OverworldScreen.COMPANION_SELECTION:
            return (enabled(OverworldAction.BACK, "Back"),)
        if screen is OverworldScreen.FLOOR_ONE_WARNING:
            return (
                enabled(OverworldAction.SET_OUT, "Set Out"),
                enabled(OverworldAction.BACK, "Back"),
            )
        if screen is OverworldScreen.PARTY_READY:
            return (
                enabled(OverworldAction.READY, "Ready / Set Out"),
                enabled(OverworldAction.BACK, "Back"),
            )
        if screen is OverworldScreen.OUTING:
            return ()
        if screen is OverworldScreen.EXTRACTION:
            return (enabled(OverworldAction.RETURN_TO_HUB, "Return to Hub"),)
        if screen is OverworldScreen.CHARACTER:
            return (
                enabled(OverworldAction.SKILLS, "Skills"),
                enabled(OverworldAction.WEAPON, "Weapon"),
                enabled(OverworldAction.EQUIPMENT, "Equipment"),
                enabled(OverworldAction.BACK, "Back"),
            )
        if screen in {
            OverworldScreen.SKILLS,
            OverworldScreen.WEAPON,
            OverworldScreen.EQUIPMENT,
            OverworldScreen.MERCHANT,
            OverworldScreen.ITEM_INSPECT,
        }:
            return (enabled(OverworldAction.BACK, "Back"),)
        if screen is OverworldScreen.ITEMS:
            return (
                disabled(
                    OverworldAction.CRAFT,
                    "Craft",
                    OverworldAvailabilityReason.CRAFT_UNAVAILABLE,
                ),
                (
                    enabled(OverworldAction.INSPECT, "Inspect")
                    if selected_item
                    else disabled(
                        OverworldAction.INSPECT,
                        "Inspect",
                        OverworldAvailabilityReason.NO_ITEM_SELECTED,
                    )
                ),
                disabled(
                    OverworldAction.USE,
                    "Use",
                    (
                        OverworldAvailabilityReason.NO_OVERWORLD_USE
                        if selected_item
                        else OverworldAvailabilityReason.NO_ITEM_SELECTED
                    ),
                ),
                enabled(OverworldAction.BACK, "Back"),
            )
        if screen is OverworldScreen.MAP:
            inspectable = get_inspectable_route_node_spec(
                game_state.overworld_state.current_route_node_id
            )
            inspect_option = (
                enabled(OverworldAction.INSPECT, "Inspect")
                if inspectable is not None
                else disabled(
                    OverworldAction.INSPECT,
                    "Inspect",
                    OverworldAvailabilityReason.ENCOUNTER_INSPECTION_UNAVAILABLE,
                )
            )
            return (inspect_option, enabled(OverworldAction.BACK, "Back"))
        if screen is OverworldScreen.MAP_INSPECT:
            return (enabled(OverworldAction.BACK, "Back"),)
        if screen is OverworldScreen.OPTIONS:
            return (
                (
                    enabled(OverworldAction.SAVE, "Save")
                    if save_available
                    else disabled(
                        OverworldAction.SAVE,
                        "Save",
                        OverworldAvailabilityReason.SAVE_UNAVAILABLE,
                    )
                ),
                enabled(OverworldAction.QUIT, "Quit"),
                (
                    enabled(OverworldAction.LOAD, "Load")
                    if load_available
                    else disabled(
                        OverworldAction.LOAD,
                        "Load",
                        OverworldAvailabilityReason.LOAD_UNAVAILABLE,
                    )
                ),
                enabled(OverworldAction.BACK, "Back"),
            )
        if screen in {
            OverworldScreen.QUIT_CONFIRMATION,
            OverworldScreen.LOAD_CONFIRMATION,
        }:
            return (
                enabled(OverworldAction.CONFIRM, "Confirm"),
                enabled(OverworldAction.CANCEL, "Cancel"),
            )
        if screen is OverworldScreen.REST:
            if game_state.overworld_state.active_route_id == "floor_one":
                return (
                    enabled(OverworldAction.REST, "Recover"),
                    (
                        enabled(OverworldAction.SAVE, "Save")
                        if save_available
                        else disabled(
                            OverworldAction.SAVE,
                            "Save",
                            OverworldAvailabilityReason.SAVE_UNAVAILABLE,
                        )
                    ),
                    enabled(OverworldAction.CHARACTER, "Character"),
                    enabled(OverworldAction.ITEMS, "Items"),
                    enabled(OverworldAction.EXTRACT, "Extract"),
                )
            return (
                enabled(OverworldAction.REST, "Rest"),
                (
                    enabled(OverworldAction.SAVE, "Save")
                    if save_available
                    else disabled(
                        OverworldAction.SAVE,
                        "Save",
                        OverworldAvailabilityReason.SAVE_UNAVAILABLE,
                    )
                ),
                enabled(OverworldAction.QUIT, "Quit"),
                enabled(OverworldAction.MENU, "Menu"),
            )
        raise ValueError(f"unsupported overworld screen: {screen!r}")

    def _contextual_route_option(self, game_state, screen):
        current_node_id = game_state.overworld_state.current_route_node_id
        current_node = get_route_node_spec(current_node_id)
        unresolved_rest = current_node_id not in set(
            game_state.overworld_state.resolved_rest_node_ids
        )
        if screen is OverworldScreen.MAIN and (
            current_node.kind is RouteNodeKind.REST and unresolved_rest
        ):
            return self._enabled_option(OverworldAction.REST, "Rest")
        if screen is OverworldScreen.REST and (
            current_node.kind is RouteNodeKind.REST and unresolved_rest
        ):
            return self._enabled_option(
                OverworldAction.SKIP_REST,
                "Continue Without Rest",
            )
        if screen is not OverworldScreen.MAIN:
            return None
        phase = game_state.overworld_state.current_contextual_route_phase
        if phase is ContextualRoutePhase.ENTER_ENCOUNTER:
            return self._enabled_option(
                OverworldAction.ENTER_ENCOUNTER,
                "Enter Encounter",
            )
        if phase is ContextualRoutePhase.RETRY:
            return self._enabled_option(OverworldAction.RETRY, "Retry")
        return None

    @staticmethod
    def _enabled_option(action, label):
        return OverworldOptionView(action, label, True)

    @staticmethod
    def _disabled_option(action, label, reason):
        return OverworldOptionView(action, label, False, reason)

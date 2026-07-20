"""Pure translation from persistent session state to overworld views."""

from itertools import groupby

from app.enemies.registry import get_enemy_registration
from app.game.encounter_manifest import inspectable_encounter_for_node
from app.game.game_state import GameState
from app.game.overworld_route import (
    FIRST_SURFACE_NODE_ID,
    RouteNodeKind,
    SURFACE_ROUTE_NODES,
    route_node,
)
from app.game.overworld_state import ContextualRoutePhase
from app.items.weapon import Weapon
from app.player.run_items import owned_run_item_definitions
from app.presentation.overworld_models import (
    AccessorySlotView,
    CharacterOverviewView,
    EquipmentView,
    InventoryView,
    MapNodeState,
    MapNodeView,
    MapView,
    MapEncounterInspectionView,
    OverworldAction,
    OverworldAvailabilityReason,
    OverworldItemView,
    OverworldOptionView,
    OverworldScreen,
    OverworldView,
    SkillMoveView,
    SkillsView,
    StatBonusView,
    StatRowView,
    WeaponView,
)


STAT_ORDER = (
    ("strength", "Strength"),
    ("constitution", "Constitution"),
    ("intelligence", "Intelligence"),
    ("spirit", "Spirit"),
    ("dexterity", "Dexterity"),
    ("intuition", "Intuition"),
)


class OverworldPresenter:
    def build(
        self,
        game_state,
        *,
        screen=OverworldScreen.MAIN,
        selected_item_key=None,
        adventure_text=None,
        notice=None,
    ):
        if not isinstance(game_state, GameState):
            raise TypeError("game_state must be a GameState")
        screen = OverworldScreen(screen)
        node = route_node(game_state.overworld_state.current_route_node_id)
        adventure_text = adventure_text or self._default_adventure_text(game_state)
        items = self._inventory_items(game_state)
        selected_item = next(
            (item for item in items if item.selection_key == selected_item_key),
            None,
        )
        options = self._options(game_state, screen, selected_item)
        contextual_route_option = self._contextual_route_option(
            game_state,
            screen,
        )

        return OverworldView(
            screen=screen,
            location_label=node.display_label,
            adventure_text=adventure_text,
            notice=notice,
            options=options,
            contextual_route_option=contextual_route_option,
            character=(
                self._character_view(game_state)
                if screen is OverworldScreen.CHARACTER
                else None
            ),
            skills=(
                self._skills_view(game_state)
                if screen is OverworldScreen.SKILLS
                else None
            ),
            weapon=(
                self._weapon_view(game_state)
                if screen is OverworldScreen.WEAPON
                else None
            ),
            equipment=(
                self._equipment_view()
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
        )

    @staticmethod
    def _default_adventure_text(game_state):
        current_label = route_node(
            game_state.overworld_state.current_route_node_id
        ).display_label
        phase = game_state.overworld_state.current_contextual_route_phase
        if phase is ContextualRoutePhase.RETRY:
            return f"{current_label} still blocks the route. Regroup and try again."
        if phase is ContextualRoutePhase.NONE:
            return f"{current_label} is cleared. The route continues ahead."
        if (
            game_state.overworld_state.current_route_node_id
            == FIRST_SURFACE_NODE_ID
        ):
            return "The road through Ketlyv begins at the edge of the Goblin horde."
        return f"{current_label} awaits along the surface route."

    def _character_view(self, game_state):
        player = game_state.player_state
        level = player.level_state
        exp = player.exp_state
        threshold = level.next_threshold
        fill_bps = min(10_000, exp.current * 10_000 // threshold)
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
        )

    def _skills_view(self, game_state):
        player = game_state.player_state
        return SkillsView(
            growth_points_available=None,
            growth_message="Growth Point spending is not yet available.",
            stats=self._stats(player, increase_controls=True),
            moves=tuple(
                SkillMoveView(move.name, move.description)
                for move in player.combat_moves
            ),
        )

    @staticmethod
    def _stats(player, *, increase_controls=False):
        values = player.character.permanent_stats.as_dict()
        return tuple(
            StatRowView(
                label=label,
                value=values[name],
                increase_visible=increase_controls,
                increase_enabled=False,
                disabled_reason=(
                    OverworldAvailabilityReason.GROWTH_UNAVAILABLE
                    if increase_controls
                    else None
                ),
            )
            for name, label in STAT_ORDER
        )

    @staticmethod
    def _weapon_view(game_state):
        weapon = game_state.player_state.get_equipped("weapon")
        if not isinstance(weapon, Weapon):
            raise ValueError("the selected Drifter has no equipped signature weapon")
        bonuses = tuple(
            StatBonusView(label, weapon.stat_bonuses[name])
            for name, label in STAT_ORDER
            if name in weapon.stat_bonuses
        )
        return WeaponView(
            name=weapon.name,
            weapon_type=weapon.weapon_type,
            intended_wielder=weapon.intended_wielder,
            bonuses=bonuses,
            description=weapon.description,
        )

    @staticmethod
    def _equipment_view():
        return EquipmentView(
            necklace=AccessorySlotView("Necklace", "Empty"),
            ring=AccessorySlotView("Ring", "Empty"),
            benefits=("None",),
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
        return tuple(items)

    @staticmethod
    def _map_view(game_state):
        current_id = game_state.overworld_state.current_route_node_id
        defeated_encounters = set(game_state.world_state.defeated_encounters)
        resolved_rest_nodes = set(
            game_state.overworld_state.resolved_rest_node_ids
        )

        def is_completed(node):
            if node.kind in {RouteNodeKind.COMBAT, RouteNodeKind.BOSS}:
                return node.node_id in defeated_encounters
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
                            if is_completed(node)
                            else MapNodeState.REMAINING
                        )
                    ),
                )
                for node in SURFACE_ROUTE_NODES
            )
        )

    @staticmethod
    def _map_encounter_inspection_view(game_state):
        encounter = inspectable_encounter_for_node(
            game_state.overworld_state.current_route_node_id
        )
        if encounter is None:
            return None

        composition = []
        for archetype_id, grouped_ids in groupby(encounter.enemy_archetype_ids):
            count = sum(1 for _ in grouped_ids)
            definition = get_enemy_registration(archetype_id).definition_factory()
            composition.append(
                definition.name
                if count == 1
                else f"{count} {definition.name}s"
            )

        return MapEncounterInspectionView(
            encounter_label=route_node(encounter.encounter_id).display_label,
            composition=tuple(composition),
            boss=encounter.boss,
        )

    def _options(self, game_state, screen, selected_item):
        enabled = self._enabled_option
        disabled = self._disabled_option
        if screen is OverworldScreen.MAIN:
            return (
                enabled(OverworldAction.CHARACTER, "Character"),
                enabled(OverworldAction.ITEMS, "Items"),
                enabled(OverworldAction.MAP, "Map"),
                enabled(OverworldAction.OPTIONS, "Options"),
            )
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
            inspectable = inspectable_encounter_for_node(
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
                disabled(
                    OverworldAction.SAVE,
                    "Save",
                    OverworldAvailabilityReason.SAVE_UNAVAILABLE,
                ),
                enabled(OverworldAction.QUIT, "Quit"),
                disabled(
                    OverworldAction.LOAD,
                    "Load",
                    OverworldAvailabilityReason.LOAD_UNAVAILABLE,
                ),
                enabled(OverworldAction.BACK, "Back"),
            )
        if screen is OverworldScreen.QUIT_CONFIRMATION:
            return (
                enabled(OverworldAction.CONFIRM, "Confirm"),
                enabled(OverworldAction.CANCEL, "Cancel"),
            )
        raise ValueError(f"unsupported overworld screen: {screen!r}")

    def _contextual_route_option(self, game_state, screen):
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

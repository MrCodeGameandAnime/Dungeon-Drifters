"""Pure translation from persistent session state to overworld views."""

from app.game.game_state import GameState
from app.game.overworld_route import RouteNodeKind, SURFACE_ROUTE_NODES, route_node
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

        return OverworldView(
            screen=screen,
            location_label=node.display_label,
            adventure_text=adventure_text,
            notice=notice,
            options=options,
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
        )

    @staticmethod
    def _default_adventure_text(game_state):
        phase = game_state.overworld_state.current_contextual_route_phase
        if phase is ContextualRoutePhase.RETRY:
            return "The Goblin still blocks the road. Regroup and try again."
        if phase is ContextualRoutePhase.NONE:
            return "The first Goblin has fallen. Two more wait farther along the road."
        return "The road through Ketlyv begins at the edge of the Goblin horde."

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
        completed = set(game_state.world_state.defeated_encounters)
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
                            if node.node_id in completed
                            else MapNodeState.REMAINING
                        )
                    ),
                )
                for node in SURFACE_ROUTE_NODES
            )
        )

    def _options(self, game_state, screen, selected_item):
        enabled = self._enabled_option
        disabled = self._disabled_option
        if screen is OverworldScreen.MAIN:
            options = [
                enabled(OverworldAction.CHARACTER, "Character"),
                enabled(OverworldAction.ITEMS, "Items"),
                enabled(OverworldAction.MAP, "Map"),
                enabled(OverworldAction.OPTIONS, "Options"),
            ]
            phase = game_state.overworld_state.current_contextual_route_phase
            if phase is ContextualRoutePhase.ENTER_ENCOUNTER:
                options.append(
                    enabled(OverworldAction.ENTER_ENCOUNTER, "Enter Encounter")
                )
            elif phase is ContextualRoutePhase.RETRY:
                options.append(enabled(OverworldAction.RETRY, "Retry"))
            return tuple(options)
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
            return (
                disabled(
                    OverworldAction.INSPECT,
                    "Inspect",
                    OverworldAvailabilityReason.ENCOUNTER_INSPECTION_UNAVAILABLE,
                ),
                enabled(OverworldAction.BACK, "Back"),
            )
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

    @staticmethod
    def _enabled_option(action, label):
        return OverworldOptionView(action, label, True)

    @staticmethod
    def _disabled_option(action, label, reason):
        return OverworldOptionView(action, label, False, reason)

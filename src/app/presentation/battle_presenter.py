"""Pure translation from combat state to immutable battle views."""

from app.combat.brace import BRACE_RULES
from app.combat.cinderwrit import CINDERWRIT_MECHANIC
from app.combat.move import DamageType, MoveKind, ResourceType
from app.combat.move_presentation import MoveRole
from app.presentation.battle_models import (
    ActionAvailabilityReason,
    ActionIntent,
    ActionOptionView,
    BattleView,
    BattleVisualView,
    CombatantView,
    InteractionPhase,
    InventoryCommandOptionView,
    InventoryConfirmationView,
    InventoryAvailabilityReason,
    InventoryInspectionView,
    InventoryItemOptionView,
    MoveAvailabilityReason,
    MoveOptionView,
    SuperMeterView,
)
from app.player.character_run_state import (
    PreparedPayloadId,
)
from app.player.run_items import (
    InventoryCommand,
    inventory_recipe_for_pair,
    owned_inventory_companions,
    owned_run_item_definitions,
    run_item_definition,
)


class BattlePresenter:
    def build(
        self,
        *,
        player,
        enemy,
        combat_state,
        log_entries=(),
        interaction_phase=InteractionPhase.ACTIONS,
        selected_inventory_item_id=None,
        selected_inventory_companion_id=None,
    ):
        phase = InteractionPhase(interaction_phase)
        selected_item = self._selected_inventory_item(
            player,
            phase,
            selected_inventory_item_id,
        )
        return BattleView(
            interaction_phase=phase,
            player=self._combatant_view(player, combat_state, is_player=True),
            enemy=self._combatant_view(enemy, combat_state, is_player=False),
            super_meter=self._super_meter_view(player),
            action_options=self._action_options(player, combat_state),
            move_options=self._move_options(player, combat_state, phase),
            inventory_items=self._inventory_items(player, phase),
            selected_inventory_item=selected_item,
            inventory_commands=self._inventory_commands(player, phase, selected_item),
            inventory_inspection=self._inventory_inspection(phase, selected_item),
            inventory_companions=self._inventory_companions(
                player,
                phase,
                selected_item,
            ),
            inventory_confirmation=self._inventory_confirmation(
                player,
                phase,
                selected_item,
                selected_inventory_companion_id,
            ),
            log_entries=tuple(log_entries),
            visual=BattleVisualView(),
        )

    def _combatant_view(self, combatant, combat_state, *, is_player):
        mana_current, mana_maximum = self._relevant_mana(combatant, is_player=is_player)
        super_current, super_maximum = self._relevant_super(combatant, is_player=is_player)
        labels = []
        if combat_state.is_defending(combatant):
            labels.append("Defending")
        if combat_state.brace_incoming_protection_active(combatant):
            labels.append("Brace")
        if combat_state.arcane_overcharge_active(combatant):
            labels.append("Arcane Overcharge")
        if combat_state.arcane_instability_active(combatant):
            labels.append("Arcane Instability")
        if combat_state.gravemantle_break_active(combatant):
            labels.append("Gravemantle Break")
        if combat_state.burn_active(combatant):
            labels.append("Burn")

        return CombatantView(
            display_name=combatant.display_name,
            hp_current=combatant.health.current,
            hp_maximum=combatant.health.maximum,
            mana_current=mana_current,
            mana_maximum=mana_maximum,
            super_current=super_current,
            super_maximum=super_maximum,
            defending=combat_state.is_defending(combatant),
            temporary_labels=tuple(labels),
        )

    @staticmethod
    def _relevant_mana(combatant, *, is_player):
        resource = combatant.mana_resource
        if is_player or resource.current or resource.maximum:
            return resource.current, resource.maximum
        return None, None

    @staticmethod
    def _relevant_super(combatant, *, is_player):
        resource = combatant.super_resource
        if is_player or resource.current or combatant.generates_super:
            return resource.current, resource.maximum
        return None, None

    def _action_options(self, player, combat_state):
        regular_moves = self._regular_moves(player)
        can_defend = bool(player.can_defend)
        heal_cooldown = combat_state.heal_cooldown_remaining(player)
        has_inventory_items = bool(
            owned_run_item_definitions(player.character_run_state)
        )
        if player.health.current >= player.health.maximum:
            heal_label = "Heal - Full HP"
            heal_enabled = False
            heal_reason = ActionAvailabilityReason.FULL_HP
        elif heal_cooldown:
            heal_label = f"Heal - {heal_cooldown} actions"
            heal_enabled = False
            heal_reason = ActionAvailabilityReason.HEAL_COOLDOWN
        else:
            heal_label = "Heal"
            heal_enabled = combat_state.heal_available(player)
            heal_reason = None

        return (
            self._action_option(
                ActionIntent.ATTACK,
                1,
                "Attack",
                enabled=bool(regular_moves),
                disabled_reason=ActionAvailabilityReason.NO_REGULAR_MOVES,
            ),
            self._action_option(
                ActionIntent.DEFEND,
                2,
                "Defend",
                enabled=can_defend,
                disabled_reason=ActionAvailabilityReason.CANNOT_DEFEND,
            ),
            self._action_option(
                ActionIntent.HEAL,
                3,
                heal_label,
                enabled=heal_enabled,
                disabled_reason=heal_reason,
            ),
            self._action_option(
                ActionIntent.ITEMS,
                4,
                "Items",
                enabled=has_inventory_items,
                disabled_reason=ActionAvailabilityReason.EMPTY_INVENTORY,
            ),
            self._action_option(
                ActionIntent.ESCAPE,
                5,
                "Escape",
                enabled=False,
                disabled_reason=ActionAvailabilityReason.NOT_IMPLEMENTED,
            ),
        )

    @staticmethod
    def _inventory_items(player, phase):
        if phase != InteractionPhase.INVENTORY:
            return ()
        run_state = player.character_run_state
        return tuple(
            InventoryItemOptionView(
                item_id=definition.item_id.value,
                number=number,
                display_name=definition.display_name,
                quantity=run_state.item_quantity(definition.item_id),
                enabled=True,
            )
            for number, definition in enumerate(
                owned_run_item_definitions(run_state),
                start=1,
            )
        )

    @staticmethod
    def _selected_inventory_item(player, phase, selected_item_id):
        inventory_phases = {
            InteractionPhase.INVENTORY_ITEM,
            InteractionPhase.INVENTORY_INSPECT,
            InteractionPhase.INVENTORY_COMBINATION,
            InteractionPhase.INVENTORY_CONFIRMATION,
        }
        if phase not in inventory_phases:
            return None
        definition = run_item_definition(selected_item_id)
        if definition is None:
            return None
        quantity = player.character_run_state.item_quantity(definition.item_id)
        if quantity <= 0:
            return None
        return InventoryItemOptionView(
            item_id=definition.item_id.value,
            number=1,
            display_name=definition.display_name,
            quantity=quantity,
            enabled=True,
        )

    @staticmethod
    def _inventory_commands(player, phase, selected_item):
        if phase != InteractionPhase.INVENTORY_ITEM or selected_item is None:
            return ()
        definition = run_item_definition(selected_item.item_id)
        companions = owned_inventory_companions(
            player.character_run_state,
            selected_item.item_id,
        )
        payload_active = player.character_run_state.payload_prepared(
            PreparedPayloadId.CINDERWRIT
        )
        options = []
        for number, command in enumerate(definition.commands, start=1):
            enabled = True
            disabled_reason = None
            if command == InventoryCommand.USE and payload_active:
                enabled = False
                disabled_reason = InventoryAvailabilityReason.ALREADY_PREPARED
            elif command == InventoryCommand.USE and not companions:
                enabled = False
                disabled_reason = InventoryAvailabilityReason.MISSING_COMPANION
            options.append(
                InventoryCommandOptionView(
                    command=command,
                    number=number,
                    label=command.value.title(),
                    enabled=enabled,
                    disabled_reason=disabled_reason,
                )
            )
        return tuple(options)

    @staticmethod
    def _inventory_inspection(phase, selected_item):
        if phase != InteractionPhase.INVENTORY_INSPECT or selected_item is None:
            return None
        definition = run_item_definition(selected_item.item_id)
        return InventoryInspectionView(
            item_id=definition.item_id.value,
            display_name=definition.display_name,
            description=definition.description,
        )

    @staticmethod
    def _inventory_companions(player, phase, selected_item):
        if phase != InteractionPhase.INVENTORY_COMBINATION or selected_item is None:
            return ()
        run_state = player.character_run_state
        return tuple(
            InventoryItemOptionView(
                item_id=definition.item_id.value,
                number=number,
                display_name=definition.display_name,
                quantity=run_state.item_quantity(definition.item_id),
                enabled=True,
            )
            for number, definition in enumerate(
                owned_inventory_companions(run_state, selected_item.item_id),
                start=1,
            )
        )

    @staticmethod
    def _inventory_confirmation(
        player,
        phase,
        selected_item,
        selected_companion_id,
    ):
        if phase != InteractionPhase.INVENTORY_CONFIRMATION or selected_item is None:
            return None
        companion = run_item_definition(selected_companion_id)
        recipe = inventory_recipe_for_pair(
            selected_item.item_id,
            selected_companion_id,
        )
        if companion is None or recipe is None:
            return None
        if player.character_run_state.item_quantity(companion.item_id) <= 0:
            return None
        return InventoryConfirmationView(
            source_item_id=selected_item.item_id,
            source_display_name=selected_item.display_name,
            companion_item_id=companion.item_id.value,
            companion_display_name=companion.display_name,
            action_id=recipe.action_id.value,
            result_display_name=recipe.result_display_name,
        )

    @staticmethod
    def _action_option(intent, number, label, *, enabled, disabled_reason):
        return ActionOptionView(
            intent=intent,
            number=number,
            label=label,
            enabled=enabled,
            disabled_reason=None if enabled else disabled_reason,
        )

    def _super_meter_view(self, player):
        resource = player.super_resource
        super_moves = self._super_moves(player)
        ready = any(self._can_afford(player, move) for move in super_moves)
        fill_bps = resource.current * 10_000 // resource.maximum
        return SuperMeterView(
            current=resource.current,
            maximum=resource.maximum,
            fill_bps=fill_bps,
            ready=ready,
            activation_key="S",
            activation_offered=ready,
        )

    def _move_options(self, player, combat_state, phase):
        if phase not in {
            InteractionPhase.REGULAR_MOVES,
            InteractionPhase.HEALING_MOVES,
            InteractionPhase.SUPER_MOVES,
        }:
            return ()
        if phase == InteractionPhase.REGULAR_MOVES:
            moves = self._regular_moves(player)
        elif phase == InteractionPhase.HEALING_MOVES:
            moves = self._healing_moves(player)
        else:
            moves = self._super_moves(player)

        return tuple(
            self._move_option(player, combat_state, move, number)
            for number, move in enumerate(moves, start=1)
        )

    def _move_option(self, player, combat_state, move, number):
        resource_label = self._resource_label(move)
        tags = [self._static_category(move)]
        follow_up_bonus = combat_state.brace_follow_up_damage_bonus_percent(
            player,
            move.mechanic,
        )
        if follow_up_bonus:
            tags.append(f"Empowered +{follow_up_bonus}%")
        if move.is_spell and move.kind == MoveKind.DAMAGE:
            overcharge_bonus = combat_state.arcane_overcharge_bonus_percent(player)
            if overcharge_bonus:
                tags.append(f"Overcharged +{overcharge_bonus}%")
        cinderwrit_prepared = True
        if move.mechanic == CINDERWRIT_MECHANIC:
            cinderwrit_prepared = player.character_run_state.payload_prepared(
                PreparedPayloadId.CINDERWRIT
            )
            tags.append("Ready" if cinderwrit_prepared else "Requires Prepared Barb")
        if resource_label is not None:
            tags.append(resource_label)

        affordable = self._can_afford(player, move)
        enabled = affordable and cinderwrit_prepared
        if enabled:
            disabled_reason = None
        elif not affordable:
            disabled_reason = MoveAvailabilityReason.INSUFFICIENT_RESOURCE
        else:
            disabled_reason = MoveAvailabilityReason.REQUIRES_PREPARED_PAYLOAD
        return MoveOptionView(
            selection_key=move.name,
            number=number,
            name=move.name,
            tags=tuple(tags),
            rules_summary=self._rules_summary(move),
            resource_label=resource_label,
            enabled=enabled,
            disabled_reason=disabled_reason,
        )

    @staticmethod
    def _regular_moves(player):
        return tuple(
            move
            for move in player.combat_moves
            if move.resource_type != ResourceType.SUPER
            and move.kind in (MoveKind.DAMAGE, MoveKind.UTILITY)
        )

    @staticmethod
    def _healing_moves(player):
        return tuple(
            move
            for move in player.combat_moves
            if move.resource_type != ResourceType.SUPER
            and move.kind == MoveKind.HEALING
        )

    @staticmethod
    def _super_moves(player):
        return tuple(
            move
            for move in player.combat_moves
            if move.resource_type == ResourceType.SUPER
        )

    @staticmethod
    def _can_afford(player, move):
        if move.resource_type == ResourceType.NONE:
            return True
        if move.resource_type == ResourceType.MANA:
            return player.mana_resource.can_afford(move.resource_cost)
        if move.resource_type == ResourceType.SUPER:
            return player.super_resource.can_afford(move.resource_cost)
        return False

    @staticmethod
    def _resource_label(move):
        if move.resource_type == ResourceType.MANA:
            return f"{move.resource_cost} Mana"
        if move.resource_type == ResourceType.SUPER:
            return f"{move.resource_cost} Super"
        return None

    @staticmethod
    def _static_category(move):
        presentation = move.presentation
        role = presentation.role if presentation is not None else None
        if move.resource_type == ResourceType.SUPER or role == MoveRole.SUPER:
            return "Super"
        if move.kind == MoveKind.HEALING or role == MoveRole.HEALING:
            return "Healing"
        if move.kind == MoveKind.UTILITY or role == MoveRole.UTILITY:
            return "Utility"
        if role == MoveRole.HEAVY:
            return "Heavy"
        if (
            role == MoveRole.NORMAL
            and presentation.affinity_label is not None
            and move.damage_type == DamageType.MAGICAL
        ):
            return f"{presentation.affinity_label} Magic"
        return "Normal"

    @staticmethod
    def _rules_summary(move):
        if move.mechanic == "brace":
            return (
                "Brace against the next enemy action, reducing physical damage by "
                f"{BRACE_RULES.incoming_reduction_percent}%, and empower your next "
                f"Heavy attack by {BRACE_RULES.follow_up_damage_bonus_percent}%."
            )
        if move.presentation is not None and move.presentation.static_summary is not None:
            return move.presentation.static_summary
        return move.description

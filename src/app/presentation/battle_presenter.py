"""Pure translation from combat state to immutable battle views."""

from app.combat.brace import BRACE_RULES
from app.combat.infused_barb import INFUSED_BARB_MECHANIC
from app.combat.frost import FROST_ATTACK_MECHANIC, FROST_RULES
from app.combat.move import DamageType, MoveKind, ResourceType
from app.combat.move_presentation import MoveRole
from app.combat.status_state import StatusKind
from app.combat.storm import LIGHTNING_PALM_MECHANIC, STORM_RULES
from app.presentation.battle_models import (
    ActionAvailabilityReason,
    ActionIntent,
    ActionOptionView,
    BattleView,
    BattleVisualView,
    CombatantView,
    EnemyCombatantView,
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
    InfusionKind,
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
        combat_state,
        enemies=None,
        enemy=None,
        enemy_target_ids=None,
        enemy_display_labels=None,
        log_entries=(),
        interaction_phase=InteractionPhase.ACTIONS,
        selected_inventory_item_id=None,
        selected_inventory_companion_id=None,
    ):
        phase = InteractionPhase(interaction_phase)
        enemies = self._normalize_enemies(enemy=enemy, enemies=enemies)
        enemy_target_ids = self._metadata_values(
            enemy_target_ids,
            tuple(f"enemy_{index}" for index in range(1, len(enemies) + 1)),
            len(enemies),
            "enemy_target_ids",
        )
        enemy_display_labels = self._metadata_values(
            enemy_display_labels,
            tuple(current.display_name for current in enemies),
            len(enemies),
            "enemy_display_labels",
        )
        living_enemies = tuple(current for current in enemies if current.is_alive())
        exact_move_target = living_enemies[0] if len(living_enemies) == 1 else None
        selected_item = self._selected_inventory_item(
            player,
            phase,
            selected_inventory_item_id,
        )
        return BattleView(
            interaction_phase=phase,
            player=self._combatant_view(
                player,
                enemies[0] if len(enemies) == 1 else None,
                combat_state,
                is_player=True,
            ),
            enemies=tuple(
                self._enemy_combatant_view(
                    current,
                    player,
                    combat_state,
                    target_id=target_id,
                    display_label=display_label,
                )
                for current, target_id, display_label in zip(
                    enemies,
                    enemy_target_ids,
                    enemy_display_labels,
                    strict=True,
                )
            ),
            super_meter=self._super_meter_view(player),
            action_options=self._action_options(player, combat_state),
            move_options=self._move_options(
                player,
                exact_move_target,
                combat_state,
                phase,
            ),
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

    @staticmethod
    def _normalize_enemies(*, enemy, enemies):
        if enemy is not None and enemies is not None:
            raise ValueError("provide enemy or enemies, not both")
        if enemies is None:
            if enemy is None:
                raise ValueError("at least one enemy is required")
            return (enemy,)
        if not isinstance(enemies, tuple):
            raise TypeError("enemies must be a tuple")
        if not enemies:
            raise ValueError("at least one enemy is required")
        if len(enemies) > 4:
            raise ValueError("at most four enemies are supported")
        return enemies

    @staticmethod
    def _metadata_values(values, defaults, expected_length, name):
        if values is None:
            return defaults
        if not isinstance(values, tuple):
            raise TypeError(f"{name} must be a tuple")
        if len(values) != expected_length:
            raise ValueError(f"{name} must align with enemies")
        return values

    def _enemy_combatant_view(
        self,
        enemy,
        player,
        combat_state,
        *,
        target_id,
        display_label,
    ):
        view = self._combatant_view(
            enemy,
            player,
            combat_state,
            is_player=False,
        )
        defeated = not enemy.is_alive()
        return EnemyCombatantView(
            target_id=target_id,
            display_label=display_label,
            hp_current=view.hp_current,
            hp_maximum=view.hp_maximum,
            mana_current=view.mana_current,
            mana_maximum=view.mana_maximum,
            super_current=view.super_current,
            super_maximum=view.super_maximum,
            defending=view.defending,
            temporary_labels=("Defeated",) if defeated else view.temporary_labels,
            defeated=defeated,
        )

    def _combatant_view(self, combatant, opposing, combat_state, *, is_player):
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
        frost_count = (
            getattr(combat_state, "frost_charge_count", lambda *_: 0)(
                opposing,
                combatant,
            )
            if opposing is not None
            else 0
        )
        if frost_count:
            labels.append(f"Frost {frost_count}/3")
        frostbite_active = getattr(
            combat_state,
            "frostbite_active",
            lambda _combatant: False,
        )
        frostbite_status = getattr(
            combat_state,
            "frostbite_status",
            lambda _combatant: None,
        )
        if frostbite_active(combatant):
            labels.append(
                f"Frostbite: {frostbite_status(combatant).remaining_ticks}"
            )
        if getattr(combat_state, "frozen_active", lambda _combatant: False)(combatant):
            labels.append("Frozen")
        status_labels = {
            StatusKind.BURN: "Burn",
            StatusKind.POISON: "Poison",
            StatusKind.CONDUCTIVE: "Conductive",
            StatusKind.TURBULENCE: "Turbulence",
            StatusKind.STUN: "Stunned",
        }
        labels.extend(
            status_labels[kind]
            for kind in combat_state.active_status_kinds(combatant)
            if kind not in {
                StatusKind.FROST,
                StatusKind.FROSTBITE,
                StatusKind.FROZEN,
            }
        )

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
                enabled=True,
                disabled_reason=None,
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
            PreparedPayloadId.INFUSED_BARB
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

    def _move_options(self, player, enemy, combat_state, phase):
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
            self._move_option(player, enemy, combat_state, move, number)
            for number, move in enumerate(moves, start=1)
        )

    def _move_option(self, player, enemy, combat_state, move, number):
        resource_label = self._resource_label(move)
        tags = [self._static_category(move)]
        conductive_lightning = False
        turbulent_lightning = False
        lightning_storm = False
        if move.mechanic == LIGHTNING_PALM_MECHANIC and enemy is not None:
            conductive = combat_state.conductive_active(player, enemy)
            turbulence = combat_state.turbulence_active(player, enemy)
            lightning_storm = conductive and turbulence
            conductive_lightning = conductive and not turbulence
            turbulent_lightning = turbulence and not conductive
            tags = ["Hybrid"]
            if lightning_storm:
                tags.append("Conductive + Turbulence")
            elif conductive_lightning:
                tags.append("Conductive")
            elif turbulent_lightning:
                tags.append("Turbulence")
        if move.mechanic == FROST_ATTACK_MECHANIC:
            tags = ["Magical", "Frost"]
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
        infusion_ready = True
        if move.mechanic == INFUSED_BARB_MECHANIC:
            infusion_kind = player.character_run_state.prepared_infusion()
            infusion_ready = infusion_kind is not None
            if infusion_kind == InfusionKind.FIRE:
                tags.append("Ready: Fire")
            elif infusion_kind == InfusionKind.POISON:
                tags.append("Ready: Poison")
            else:
                tags.append("Requires Prepared Infusion")
        if resource_label is not None:
            tags.append(resource_label)

        affordable = self._can_afford(player, move)
        enabled = affordable and infusion_ready
        if enabled:
            disabled_reason = None
        elif not affordable:
            disabled_reason = MoveAvailabilityReason.INSUFFICIENT_RESOURCE
        else:
            disabled_reason = MoveAvailabilityReason.REQUIRES_PREPARED_PAYLOAD
        return MoveOptionView(
            selection_key=move.name,
            number=number,
            name="Lightning Storm" if lightning_storm else move.name,
            tags=tuple(tags),
            rules_summary=self._rules_summary(
                move,
                conductive_lightning,
                turbulent_lightning,
                lightning_storm,
            ),
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
    def _rules_summary(
        move,
        conductive_lightning=False,
        turbulent_lightning=False,
        lightning_storm=False,
    ):
        if move.mechanic == "brace":
            return (
                "Brace against the next enemy action, reducing physical damage by "
                f"{BRACE_RULES.incoming_reduction_percent}%, and empower your next "
                f"Heavy attack by {BRACE_RULES.follow_up_damage_bonus_percent}%."
            )
        if move.mechanic == LIGHTNING_PALM_MECHANIC and conductive_lightning:
            return (
                "Consume Conductive for "
                f"{STORM_RULES.conductive_damage_bonus_percent}% increased damage "
                f"and a {STORM_RULES.stun_chance_percent}% chance to Stun."
            )
        if move.mechanic == LIGHTNING_PALM_MECHANIC and lightning_storm:
            return (
                "Consume Conductive and Turbulence for "
                f"{STORM_RULES.lightning_storm_damage_bonus_percent}% increased damage."
            )
        if move.mechanic == LIGHTNING_PALM_MECHANIC and turbulent_lightning:
            return (
                "Consume Turbulence for "
                f"{STORM_RULES.turbulence_damage_bonus_percent}% increased damage."
            )
        if move.mechanic == FROST_ATTACK_MECHANIC:
            return (
                "Landed hits apply Frost. At 3 Frost, the target becomes Frozen "
                f"and suffers Frostbite for {FROST_RULES.frostbite_duration_ticks} "
                "accepted actions."
            )
        if move.presentation is not None and move.presentation.static_summary is not None:
            return move.presentation.static_summary
        return move.description

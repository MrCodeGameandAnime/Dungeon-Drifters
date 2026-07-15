"""Pure translation from combat state to immutable battle views."""

from app.combat.brace import BRACE_RULES
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
    MoveAvailabilityReason,
    MoveOptionView,
    SuperMeterView,
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
    ):
        phase = InteractionPhase(interaction_phase)
        return BattleView(
            interaction_phase=phase,
            player=self._combatant_view(player, combat_state, is_player=True),
            enemy=self._combatant_view(enemy, combat_state, is_player=False),
            super_meter=self._super_meter_view(player),
            action_options=self._action_options(player),
            move_options=self._move_options(player, combat_state, phase),
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

    def _action_options(self, player):
        regular_moves = self._regular_moves(player)
        healing_moves = self._healing_moves(player)
        can_defend = bool(player.can_defend)
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
                "Heal",
                enabled=bool(healing_moves),
                disabled_reason=ActionAvailabilityReason.NO_HEALING_MOVES,
            ),
            self._action_option(
                ActionIntent.ITEMS,
                4,
                "Items",
                enabled=False,
                disabled_reason=ActionAvailabilityReason.NOT_IMPLEMENTED,
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
        if phase == InteractionPhase.ACTIONS:
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
        if resource_label is not None:
            tags.append(resource_label)

        enabled = self._can_afford(player, move)
        return MoveOptionView(
            selection_key=move.name,
            number=number,
            name=move.name,
            tags=tuple(tags),
            rules_summary=self._rules_summary(move),
            resource_label=resource_label,
            enabled=enabled,
            disabled_reason=(
                None
                if enabled
                else MoveAvailabilityReason.INSUFFICIENT_RESOURCE
            ),
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

import random

from app.combat.combat_state import CombatState
from app.combat.move import TargetType
from app.combat.resolver import CombatResolver
from app.presentation.battle_models import (
    ActionIntent,
    BattleEventType,
    BattleLogEntry,
    InputRejectionReason,
    InteractionPhase,
)
from app.presentation.battle_presenter import BattlePresenter
from app.presentation.battle_session import BattlePresentationSession
from app.player.inventory_action import InventoryActionResolver
from app.player.run_items import InventoryCommand
from app.ui.battle_ui import (
    ChooseAction,
    ChooseInventoryCommand,
    ChooseInventoryCompanion,
    ChooseInventoryItem,
    ChooseMove,
    ConfirmInventoryUse,
    GoBack,
)


class Battle:
    def __init__(
        self,
        player_state,
        foe,
        ui,
        resolver=None,
        presenter=None,
        presentation_session=None,
        inventory_action_resolver=None,
    ):
        self.player_state = player_state
        self.player = player_state.character
        self.foe = foe
        self.combat_state = CombatState()
        self.resolver = resolver or CombatResolver()
        self.ui = ui
        self.presenter = presenter or BattlePresenter()
        self.presentation_session = presentation_session or BattlePresentationSession()
        self.inventory_action_resolver = (
            inventory_action_resolver or InventoryActionResolver()
        )
        self.interaction_phase = InteractionPhase.ACTIONS
        self._selected_inventory_item_id = None
        self._selected_inventory_companion_id = None

    def _player_moves(self):
        return self.player_state.combat_moves

    def _enemy_moves(self):
        return self.foe.combat_moves

    def _complete_accepted_action(
        self,
        actor,
        opposing_combatants,
        result,
        *,
        reduce_heal_cooldown=True,
    ):
        if result.accepted:
            if reduce_heal_cooldown:
                outcomes = self.combat_state.complete_accepted_action(
                    actor,
                    opposing_combatants,
                )
            else:
                outcomes = self.combat_state.complete_accepted_action(
                    actor,
                    opposing_combatants,
                    reduce_heal_cooldown=False,
                )
            if outcomes:
                self._record_lifecycle_outcomes(
                    actor,
                    opposing_combatants,
                    outcomes,
                )
            return outcomes

        return None

    def _record_lifecycle_outcomes(self, actor, opposing_combatants, outcomes):
        target = next(
            (combatant for combatant in opposing_combatants if combatant is not actor),
            None,
        )
        self.presentation_session.record(
            BattleLogEntry(
                event_type=BattleEventType.STATUS,
                actor_name=actor.display_name,
                target_name=target.display_name if target is not None else None,
                outcomes=outcomes,
            )
        )

    def _player_target_for_move(self, move):
        if move.target == TargetType.ENEMY:
            return self.foe
        if move.target == TargetType.SELF:
            return self.player_state

        raise ValueError(f"Unsupported player move target: {move.target!r}")

    def _resolve_player_move(self, move):
        target = self._player_target_for_move(move)
        result = self.resolver.resolve_move(
            self.player_state,
            target,
            move.name,
            combat_state=self.combat_state,
            character_run_state=self.player_state.character_run_state,
        )
        if result.accepted:
            self.presentation_session.begin_player_turn()
        self._record_move_result(result, actor=self.player_state, target=target)
        return result

    def _enemy_target_for_move(self, move):
        if move.target == TargetType.ENEMY:
            return self.player_state
        if move.target == TargetType.SELF:
            return self.foe

        raise ValueError(f"Unsupported enemy move target: {move.target!r}")

    def _resolve_enemy_move(self, move):
        target = self._enemy_target_for_move(move)
        result = self.resolver.resolve_move(
            self.foe,
            target,
            move.name,
            combat_state=self.combat_state,
        )
        self._record_move_result(result, actor=self.foe, target=target)
        return result

    def _record_move_result(self, result, actor, target=None, event_type=None):
        self.presentation_session.record(
            BattleLogEntry(
                event_type=event_type or self._event_type_for_result(result),
                actor_name=actor.display_name,
                target_name=target.display_name if target is not None else None,
                action_name=result.move_name,
                accepted=result.accepted,
                hit=result.hit,
                amount=result.damage or result.healing,
                critical=result.critical,
                resource_spent=result.resource_spent,
                statuses_applied=result.statuses_applied,
                reason=result.reason,
                outcomes=result.outcomes,
            )
        )

    @staticmethod
    def _event_type_for_result(result):
        if not result.accepted:
            return BattleEventType.ACTION_REJECTED
        if not result.hit:
            return BattleEventType.MISS
        if result.damage:
            return BattleEventType.DAMAGE
        if result.healing:
            return BattleEventType.HEALING
        return BattleEventType.UTILITY

    def _build_view(self):
        return self.presenter.build(
            player=self.player_state,
            enemy=self.foe,
            combat_state=self.combat_state,
            log_entries=self.presentation_session.entries,
            interaction_phase=self.interaction_phase,
            selected_inventory_item_id=self._selected_inventory_item_id,
            selected_inventory_companion_id=self._selected_inventory_companion_id,
        )

    def _render_current_view(self):
        view = self._build_view()
        self.ui.render(view)
        return view

    def run(self):
        self.presentation_session.record(
            BattleLogEntry(
                event_type=BattleEventType.ENCOUNTER_START,
                target_name=self.foe.display_name,
            )
        )

        player_turn = random.randint(1, 2) == 1
        first_actor = self.player_state if player_turn else self.foe
        self.presentation_session.record(
            BattleLogEntry(
                event_type=BattleEventType.INITIATIVE,
                actor_name=first_actor.display_name,
            )
        )

        while self.player_state.is_alive() and self.foe.is_alive():
            current_actor = self.player_state if player_turn else self.foe
            if self._skip_action_opportunity_suppression(current_actor):
                player_turn = not player_turn
                continue
            if player_turn:
                action_accepted = self.player_action()
            else:
                action_accepted = self.enemy_action()

            if action_accepted:
                player_turn = not player_turn

        player_won = not self.foe.is_alive() and self.player_state.is_alive()
        self.presentation_session.record(
            BattleLogEntry(
                event_type=(
                    BattleEventType.VICTORY
                    if player_won
                    else BattleEventType.DEFEAT
                ),
                actor_name=self.player_state.display_name,
                target_name=self.foe.display_name,
            )
        )
        self.interaction_phase = InteractionPhase.ACTIONS
        self._clear_inventory_navigation()
        self._render_current_view()
        return "player" if player_won else "enemy"

    def _skip_stunned_action_opportunity(self, actor):
        return self._skip_action_opportunity_suppression(actor)

    def _skip_action_opportunity_suppression(self, actor):
        outcomes = self.combat_state.consume_action_opportunity_suppression(actor)
        if not outcomes:
            return False
        opposing = self.foe if actor is self.player_state else self.player_state
        self.presentation_session.record(
            BattleLogEntry(
                event_type=BattleEventType.STATUS,
                actor_name=actor.display_name,
                target_name=opposing.display_name,
                outcomes=outcomes,
            )
        )
        return True

    def player_action(self):
        self.interaction_phase = InteractionPhase.ACTIONS
        self._clear_inventory_navigation()
        while True:
            view = self._render_current_view()
            battle_input = self.ui.read_input(view)
            rejection_reason = self._input_rejection_reason(view, battle_input)
            if rejection_reason is not None:
                self._record_input_rejection(rejection_reason)
                continue

            if isinstance(battle_input, ChooseAction):
                if battle_input.intent == ActionIntent.ATTACK:
                    self._clear_inventory_navigation()
                    self.interaction_phase = InteractionPhase.REGULAR_MOVES
                    continue
                if battle_input.intent == ActionIntent.HEAL:
                    result = self.resolver.resolve_heal(
                        self.player_state,
                        combat_state=self.combat_state,
                    )
                    if result.accepted:
                        self.presentation_session.begin_player_turn()
                    self._record_move_result(result, actor=self.player_state)
                    if result.accepted:
                        self._complete_accepted_action(
                            self.player_state,
                            (self.foe,),
                            result,
                            reduce_heal_cooldown=False,
                        )
                        self.interaction_phase = InteractionPhase.ACTIONS
                        return True
                    continue
                if battle_input.intent == ActionIntent.SUPER:
                    self._clear_inventory_navigation()
                    self.interaction_phase = InteractionPhase.SUPER_MOVES
                    continue
                if battle_input.intent == ActionIntent.ITEMS:
                    self._clear_inventory_navigation()
                    self.interaction_phase = InteractionPhase.INVENTORY
                    continue
                if battle_input.intent == ActionIntent.DEFEND:
                    result = self.resolver.resolve_defend(
                        self.player_state,
                        self.combat_state,
                    )
                    if result.accepted:
                        self.presentation_session.begin_player_turn()
                    self._record_move_result(
                        result,
                        actor=self.player_state,
                        event_type=(
                            BattleEventType.DEFEND
                            if result.accepted
                            else BattleEventType.ACTION_REJECTED
                        ),
                    )
                    if result.accepted:
                        self._complete_accepted_action(
                            self.player_state,
                            (self.foe,),
                            result,
                        )
                        self.interaction_phase = InteractionPhase.ACTIONS
                        return True
                    continue

            if isinstance(battle_input, GoBack):
                self._navigate_back()
                continue

            if isinstance(battle_input, ChooseInventoryItem):
                self._selected_inventory_item_id = battle_input.item_id
                self._selected_inventory_companion_id = None
                self.interaction_phase = InteractionPhase.INVENTORY_ITEM
                continue

            if isinstance(battle_input, ChooseInventoryCommand):
                self._selected_inventory_companion_id = None
                if battle_input.command == InventoryCommand.INSPECT:
                    self.interaction_phase = InteractionPhase.INVENTORY_INSPECT
                else:
                    self.interaction_phase = InteractionPhase.INVENTORY_COMBINATION
                continue

            if isinstance(battle_input, ChooseInventoryCompanion):
                self._selected_inventory_companion_id = battle_input.item_id
                self.interaction_phase = InteractionPhase.INVENTORY_CONFIRMATION
                continue

            if isinstance(battle_input, ConfirmInventoryUse):
                if not battle_input.confirmed:
                    self._selected_inventory_companion_id = None
                    self.interaction_phase = InteractionPhase.INVENTORY_ITEM
                    continue
                confirmation = view.inventory_confirmation
                result = self.inventory_action_resolver.resolve(
                    confirmation.action_id,
                    self.player_state.character_run_state,
                )
                if result.accepted:
                    self.presentation_session.begin_player_turn()
                self._record_inventory_action_result(result)
                if result.accepted:
                    self._complete_accepted_action(
                        self.player_state,
                        (self.foe,),
                        result,
                    )
                    self.interaction_phase = InteractionPhase.ACTIONS
                    self._clear_inventory_navigation()
                    return True
                continue

            if isinstance(battle_input, ChooseMove):
                move = self._move_for_key(view, battle_input.move_key)
                result = self._resolve_player_move(move)
                if result.accepted:
                    self._complete_accepted_action(
                        self.player_state,
                        (self.foe,),
                        result,
                    )
                    self.interaction_phase = InteractionPhase.ACTIONS
                    self._clear_inventory_navigation()
                    return True

    def _navigate_back(self):
        if self.interaction_phase == InteractionPhase.INVENTORY_ITEM:
            self.interaction_phase = InteractionPhase.INVENTORY
            self._clear_inventory_navigation()
            return
        if self.interaction_phase in {
            InteractionPhase.INVENTORY_INSPECT,
            InteractionPhase.INVENTORY_COMBINATION,
        }:
            self.interaction_phase = InteractionPhase.INVENTORY_ITEM
            self._selected_inventory_companion_id = None
            return
        if self.interaction_phase == InteractionPhase.INVENTORY_CONFIRMATION:
            self.interaction_phase = InteractionPhase.INVENTORY_COMBINATION
            self._selected_inventory_companion_id = None
            return
        self.interaction_phase = InteractionPhase.ACTIONS
        self._clear_inventory_navigation()

    def _clear_inventory_navigation(self):
        self._selected_inventory_item_id = None
        self._selected_inventory_companion_id = None

    def _move_for_key(self, view, move_key):
        for option in view.move_options:
            if option.selection_key == move_key:
                for move in self._player_moves():
                    if move.name == option.selection_key:
                        return move
        raise ValueError("move key was not offered")

    def _record_inventory_action_result(self, result):
        self.presentation_session.record(
            BattleLogEntry(
                event_type=BattleEventType.INVENTORY,
                actor_name=self.player_state.display_name,
                action_name=result.action_id.value,
                accepted=result.accepted,
                reason=result.reason.value if result.reason is not None else None,
                outcomes=result.outcomes,
            )
        )

    def _input_rejection_reason(self, view, battle_input):
        if isinstance(battle_input, ChooseAction):
            if battle_input.intent == ActionIntent.SUPER:
                if view.super_meter.activation_offered:
                    return None
                return InputRejectionReason.SUPER_UNAVAILABLE
            if view.interaction_phase != InteractionPhase.ACTIONS:
                return InputRejectionReason.ACTION_UNAVAILABLE
            if any(
                option.intent == battle_input.intent and option.enabled
                for option in view.action_options
            ):
                return None
            return InputRejectionReason.ACTION_UNAVAILABLE

        if isinstance(battle_input, ChooseMove):
            if view.interaction_phase == InteractionPhase.ACTIONS:
                return InputRejectionReason.MOVE_UNAVAILABLE
            if any(
                option.selection_key == battle_input.move_key and option.enabled
                for option in view.move_options
            ):
                return None
            return InputRejectionReason.MOVE_UNAVAILABLE

        if isinstance(battle_input, ChooseInventoryItem):
            if view.interaction_phase != InteractionPhase.INVENTORY:
                return InputRejectionReason.INVENTORY_ITEM_UNAVAILABLE
            if any(
                option.item_id == battle_input.item_id and option.enabled
                for option in view.inventory_items
            ):
                return None
            return InputRejectionReason.INVENTORY_ITEM_UNAVAILABLE

        if isinstance(battle_input, ChooseInventoryCommand):
            if view.interaction_phase != InteractionPhase.INVENTORY_ITEM:
                return InputRejectionReason.INVENTORY_COMMAND_UNAVAILABLE
            if any(
                option.command == battle_input.command and option.enabled
                for option in view.inventory_commands
            ):
                return None
            return InputRejectionReason.INVENTORY_COMMAND_UNAVAILABLE

        if isinstance(battle_input, ChooseInventoryCompanion):
            if view.interaction_phase != InteractionPhase.INVENTORY_COMBINATION:
                return InputRejectionReason.INVENTORY_COMPANION_UNAVAILABLE
            if any(
                option.item_id == battle_input.item_id and option.enabled
                for option in view.inventory_companions
            ):
                return None
            return InputRejectionReason.INVENTORY_COMPANION_UNAVAILABLE

        if isinstance(battle_input, ConfirmInventoryUse):
            if (
                view.interaction_phase == InteractionPhase.INVENTORY_CONFIRMATION
                and view.inventory_confirmation is not None
            ):
                return None
            return InputRejectionReason.INVENTORY_CONFIRMATION_UNAVAILABLE

        if isinstance(battle_input, GoBack):
            if view.interaction_phase != InteractionPhase.ACTIONS:
                return None
            return InputRejectionReason.BACK_UNAVAILABLE

        return InputRejectionReason.ACTION_UNAVAILABLE

    def _record_input_rejection(self, reason):
        self.presentation_session.record(
            BattleLogEntry(
                event_type=BattleEventType.INPUT_REJECTED,
                rejection_reason=reason,
            )
        )

    def enemy_action(self):
        move = random.choice(list(self._enemy_moves()))
        result = self._resolve_enemy_move(move)
        if result.accepted:
            self._complete_accepted_action(
                self.foe,
                (self.player_state,),
                result,
            )

        return result.accepted

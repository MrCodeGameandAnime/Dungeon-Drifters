"""Stateless terminal rendering and semantic input translation."""

import builtins

from app.presentation.battle_models import (
    ActionIntent,
    BattleEventType,
    BattleView,
    InputRejectionReason,
    InteractionPhase,
)
from app.ui.battle_ui import ChooseAction, ChooseMove, GoBack


class TerminalBattleUI:
    def __init__(self, *, input_func=None, output_func=None):
        self._input = input_func or builtins.input
        self._output = output_func or builtins.print

    def render(self, view):
        if not isinstance(view, BattleView):
            raise TypeError("view must be a BattleView")

        self._render_combatant(view.player)
        self._render_combatant(view.enemy)
        for entry in view.log_entries:
            for line in self._log_lines(entry):
                self._output(line)

        if view.interaction_phase == InteractionPhase.ACTIONS:
            self._output("Choose an action:")
            for option in view.action_options:
                suffix = "" if option.enabled else " [Unavailable]"
                self._output(f"{option.number}. {option.label}{suffix}")
        else:
            self._output(self._phase_heading(view.interaction_phase))
            for move in view.move_options:
                tags = " | ".join(move.tags)
                suffix = "" if move.enabled else " [Unavailable]"
                self._output(f"{move.number}. {move.name} [{tags}]{suffix}")
            self._output("0. Back")

        meter = view.super_meter
        ready = " READY [S]" if meter.activation_offered else ""
        self._output(f"Super: {meter.current}/{meter.maximum}{ready}")

    def read_input(self, view):
        if not isinstance(view, BattleView):
            raise TypeError("view must be a BattleView")

        while True:
            raw_value = self._input("> ")
            if not isinstance(raw_value, str):
                self._output("That is not a valid move. Please try again.")
                continue

            choice = raw_value.strip().lower()
            selected = self._translate_choice(view, choice)
            if selected is not None:
                return selected

            self._output("That is not a valid move. Please try again.")

    def _translate_choice(self, view, choice):
        if choice in ("s", "super"):
            if view.super_meter.activation_offered:
                return ChooseAction(ActionIntent.SUPER)
            self._output("Super is not available.")
            return None

        if view.interaction_phase == InteractionPhase.ACTIONS:
            return self._translate_action(view, choice)

        if choice in ("0", "back"):
            return GoBack()
        return self._translate_move(view, choice)

    def _translate_action(self, view, choice):
        for option in view.action_options:
            if choice not in (str(option.number), option.label.lower(), option.intent.value):
                continue
            if option.enabled:
                return ChooseAction(option.intent)
            self._output(f"{option.label} is not available.")
            return None
        return None

    def _translate_move(self, view, choice):
        for move in view.move_options:
            if choice not in (str(move.number), move.name.lower()):
                continue
            if move.enabled:
                return ChooseMove(move.selection_key)
            self._output(f"{move.name} is not available.")
            return None
        return None

    def _render_combatant(self, combatant):
        self._output(
            f"{combatant.display_name} HP: "
            f"{combatant.hp_current}/{combatant.hp_maximum}"
        )
        if combatant.mana_current is not None:
            self._output(
                f"{combatant.display_name} Mana: "
                f"{combatant.mana_current}/{combatant.mana_maximum}"
            )
        if combatant.super_current is not None:
            self._output(
                f"{combatant.display_name} Super: "
                f"{combatant.super_current}/{combatant.super_maximum}"
            )
        for label in combatant.temporary_labels:
            self._output(f"{combatant.display_name} {label}: yes")

    @staticmethod
    def _phase_heading(phase):
        if phase == InteractionPhase.SUPER_MOVES:
            return "Choose a Super:"
        return "Choose a move:"

    def _log_lines(self, entry):
        actor = entry.actor_name or "Combatant"
        target = entry.target_name or "target"
        action = entry.action_name or "action"
        if entry.event_type == BattleEventType.ENCOUNTER_START:
            return (f"A {target} blocks your path!",)
        if entry.event_type == BattleEventType.INITIATIVE:
            return (f"{actor} will go first.",)
        if entry.event_type == BattleEventType.DAMAGE:
            critical = " Critical hit!" if entry.critical else ""
            return (f"{actor} used {action}.{critical} It dealt {entry.amount} damage.",)
        if entry.event_type == BattleEventType.MISS:
            return (f"{actor} used {action}, but missed.",)
        if entry.event_type == BattleEventType.HEALING:
            return (f"{actor} used {action}. It restored {entry.amount} health.",)
        if entry.event_type == BattleEventType.DEFEND:
            return (f"{actor} used Defend.",)
        if entry.event_type == BattleEventType.UTILITY:
            return (f"{actor} used {action}. It resolved.",)
        if entry.event_type == BattleEventType.ACTION_REJECTED:
            return (f"{actor} used {action}, but it failed: {entry.reason}.",)
        if entry.event_type == BattleEventType.INPUT_REJECTED:
            return (self._input_rejection_text(entry.rejection_reason),)
        if entry.event_type == BattleEventType.VICTORY:
            return (f"{actor} is victorious over {target}.",)
        if entry.event_type == BattleEventType.DEFEAT:
            return (f"{actor} was defeated by {target}.",)
        raise ValueError(f"unsupported battle event type: {entry.event_type!r}")

    @staticmethod
    def _input_rejection_text(reason):
        if reason == InputRejectionReason.SUPER_UNAVAILABLE:
            return "Super is not available."
        if reason == InputRejectionReason.MOVE_UNAVAILABLE:
            return "That move is not available."
        if reason == InputRejectionReason.BACK_UNAVAILABLE:
            return "Back is not available."
        return "That action is not available."

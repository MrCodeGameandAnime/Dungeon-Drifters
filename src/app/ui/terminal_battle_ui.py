"""Stateless terminal rendering and semantic input translation."""

import builtins
import shutil
import textwrap

from app.presentation.battle_models import (
    ActionIntent,
    BattleEventType,
    BattleView,
    InputRejectionReason,
    InteractionPhase,
)
from app.ui.battle_ui import ChooseAction, ChooseMove, GoBack


class TerminalBattleUI:
    def __init__(self, *, input_func=None, output_func=None, width_provider=None):
        self._input = input_func or (lambda prompt: builtins.input(prompt))
        self._output = output_func or (lambda message: builtins.print(message))
        self._width_provider = width_provider or (
            lambda: shutil.get_terminal_size((80, 24)).columns
        )

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
                for line in textwrap.wrap(
                    move.rules_summary,
                    width=max(20, self._width_provider() - 3),
                    break_long_words=False,
                    break_on_hyphens=False,
                ):
                    self._output(f"   {line}")
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
        lines = []
        if entry.event_type == BattleEventType.ENCOUNTER_START:
            lines.append(f"A {target} blocks your path!")
        elif entry.event_type == BattleEventType.INITIATIVE:
            lines.append(f"{actor} will go first.")
        elif entry.event_type == BattleEventType.DAMAGE:
            critical = " Critical hit!" if entry.critical else ""
            lines.append(f"{actor} used {action}.{critical} It dealt {entry.amount} damage.")
        elif entry.event_type == BattleEventType.MISS:
            lines.append(f"{actor} used {action}, but missed.")
        elif entry.event_type == BattleEventType.HEALING:
            lines.append(f"{actor} used {action}. It restored {entry.amount} health.")
        elif entry.event_type == BattleEventType.DEFEND:
            lines.append(f"{actor} used Defend.")
        elif entry.event_type == BattleEventType.UTILITY:
            lines.append(f"{actor} used {action}. It resolved.")
        elif entry.event_type == BattleEventType.ACTION_REJECTED:
            lines.append(f"{actor} used {action}, but it failed: {entry.reason}.")
        elif entry.event_type == BattleEventType.INPUT_REJECTED:
            lines.append(self._input_rejection_text(entry.rejection_reason))
        elif entry.event_type == BattleEventType.VICTORY:
            lines.append(f"{actor} is victorious over {target}.")
        elif entry.event_type == BattleEventType.DEFEAT:
            lines.append(f"{actor} was defeated by {target}.")
        else:
            raise ValueError(f"unsupported battle event type: {entry.event_type!r}")

        if entry.resource_spent:
            lines.append(f"Resource spent: {entry.resource_spent}.")
        if entry.statuses_applied:
            lines.append(f"Statuses applied: {', '.join(entry.statuses_applied)}.")
        return tuple(lines)

    @staticmethod
    def _input_rejection_text(reason):
        if reason == InputRejectionReason.SUPER_UNAVAILABLE:
            return "Super is not available."
        if reason == InputRejectionReason.MOVE_UNAVAILABLE:
            return "That move is not available."
        if reason == InputRejectionReason.BACK_UNAVAILABLE:
            return "Back is not available."
        return "That action is not available."

"""Stateless terminal rendering and semantic input translation."""

import builtins
import shutil
import sys
import textwrap

from app.presentation.battle_models import (
    ActionIntent,
    BattleEventType,
    BattleView,
    InputRejectionReason,
    InteractionPhase,
)
from app.combat.result import CombatOutcomeTarget, CombatOutcomeType
from app.ui.battle_ui import (
    ChooseAction,
    ChooseInventoryCommand,
    ChooseInventoryCompanion,
    ChooseInventoryItem,
    ChooseMove,
    ConfirmInventoryUse,
    GoBack,
)


class TerminalBattleUI:
    VISIBLE_LOG_LINES = 12
    _ACTION_KEYS = {
        ActionIntent.ATTACK: "A",
        ActionIntent.DEFEND: "D",
        ActionIntent.HEAL: "H",
        ActionIntent.ITEMS: "I",
        ActionIntent.ESCAPE: "E",
        ActionIntent.SUPER: "S",
    }

    def __init__(
        self,
        *,
        input_func=None,
        output_func=None,
        width_provider=None,
        unicode_enabled=True,
        ansi_enabled=None,
        interactive=None,
    ):
        self._input = input_func or (lambda prompt: builtins.input(prompt))
        self._output = output_func or (lambda message: builtins.print(message))
        self._width_provider = width_provider or (
            lambda: shutil.get_terminal_size((80, 24)).columns
        )
        self._unicode_enabled = bool(unicode_enabled)
        if interactive is None:
            interactive = sys.stdin.isatty() and sys.stdout.isatty()
        if ansi_enabled is None:
            ansi_enabled = interactive
        self._ansi_enabled = bool(ansi_enabled)
        self._interactive = bool(interactive)

    def render(self, view):
        if not isinstance(view, BattleView):
            raise TypeError("view must be a BattleView")

        width = max(30, int(self._width_provider()))
        lines = (
            self._framed_lines(view, width)
            if width >= 60
            else self._linear_lines(view, width)
        )
        if self._interactive and self._ansi_enabled:
            lines = ("\033[2J\033[H" + lines[0], *lines[1:])
        for line in lines:
            self._output(line)

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
            self._output("Super is not ready.")
            return None

        if view.interaction_phase == InteractionPhase.ACTIONS:
            return self._translate_action(view, choice)

        if choice in ("0", "back"):
            return GoBack()
        if view.interaction_phase == InteractionPhase.INVENTORY:
            return self._translate_inventory_item(view, choice)
        if view.interaction_phase == InteractionPhase.INVENTORY_ITEM:
            return self._translate_inventory_command(view, choice)
        if view.interaction_phase == InteractionPhase.INVENTORY_COMBINATION:
            return self._translate_inventory_companion(view, choice)
        if view.interaction_phase == InteractionPhase.INVENTORY_CONFIRMATION:
            if choice in ("y", "yes", "1"):
                return ConfirmInventoryUse(True)
            if choice in ("n", "no", "2"):
                return ConfirmInventoryUse(False)
            return None
        if view.interaction_phase == InteractionPhase.INVENTORY_INSPECT:
            return None
        return self._translate_move(view, choice)

    def _translate_action(self, view, choice):
        for option in view.action_options:
            action_key = self._ACTION_KEYS[option.intent].lower()
            if choice not in (
                action_key,
                str(option.number),
                option.label.lower(),
                option.intent.value,
            ):
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

    def _translate_inventory_item(self, view, choice):
        for option in view.inventory_items:
            if choice not in (
                str(option.number),
                option.display_name.lower(),
                option.item_id,
            ):
                continue
            if option.enabled:
                return ChooseInventoryItem(option.item_id)
            self._output(f"{option.display_name} is not available.")
            return None
        return None

    def _translate_inventory_command(self, view, choice):
        for option in view.inventory_commands:
            if choice not in (
                str(option.number),
                option.label.lower(),
                option.command.value,
            ):
                continue
            if option.enabled:
                return ChooseInventoryCommand(option.command)
            self._output(f"{option.label} is not available.")
            return None
        return None

    def _translate_inventory_companion(self, view, choice):
        for option in view.inventory_companions:
            if choice not in (
                str(option.number),
                option.display_name.lower(),
                option.item_id,
            ):
                continue
            if option.enabled:
                return ChooseInventoryCompanion(option.item_id)
            self._output(f"{option.display_name} is not available.")
            return None
        return None

    def _framed_lines(self, view, width):
        chars = self._frame_characters()
        lines = [chars["top_left"] + chars["horizontal"] * (width - 2) + chars["top_right"]]
        sections = (
            self._status_lines(view, width - 4),
            self._visual_lines(view, width - 4),
            self._display_log_lines(view, width - 4),
            self._control_lines(view, width - 4),
            (self._super_meter_line(view, width - 4),),
        )
        for section_index, section in enumerate(sections):
            if section_index:
                lines.append(
                    chars["middle_left"]
                    + chars["horizontal"] * (width - 2)
                    + chars["middle_right"]
                )
            for content in section:
                lines.append(self._boxed_line(content, width, chars["vertical"]))
        lines.append(chars["bottom_left"] + chars["horizontal"] * (width - 2) + chars["bottom_right"])
        return tuple(lines)

    def _linear_lines(self, view, width):
        lines = ["STATUS"]
        lines.extend(self._combatant_status(view.player, include_super=False))
        lines.extend(self._combatant_status(view.enemy, include_super=True))
        lines.append("VISUALS")
        lines.extend(self._visual_lines(view, width))
        lines.append("BATTLE LOG")
        lines.extend(self._display_log_lines(view, width))
        lines.append("ACTIONS")
        lines.extend(self._control_lines(view, width))
        lines.append(self._super_meter_line(view, width))
        return tuple(
            wrapped
            for line in lines
            for wrapped in self._wrap(line, width)
        )

    def _status_lines(self, view, width):
        player_lines = self._combatant_status(view.player, include_super=False)
        enemy_lines = self._combatant_status(view.enemy, include_super=True)
        separator = " │ " if self._unicode_enabled else " | "
        left_width = (width - len(separator)) // 2
        right_width = width - len(separator) - left_width
        rows = []
        for index in range(max(len(player_lines), len(enemy_lines))):
            left = player_lines[index] if index < len(player_lines) else ""
            right = enemy_lines[index] if index < len(enemy_lines) else ""
            rows.append(
                self._fit(left, left_width).ljust(left_width)
                + separator
                + self._fit(right, right_width)
            )
        return tuple(rows)

    @staticmethod
    def _combatant_status(combatant, *, include_super):
        lines = [combatant.display_name, f"HP {combatant.hp_current}/{combatant.hp_maximum}"]
        if combatant.mana_current is not None:
            lines.append(f"Mana {combatant.mana_current}/{combatant.mana_maximum}")
        if include_super and combatant.super_current is not None:
            lines.append(f"Super {combatant.super_current}/{combatant.super_maximum}")
        if combatant.temporary_labels:
            lines.append("State: " + ", ".join(combatant.temporary_labels))
        return tuple(lines)

    def _visual_lines(self, view, width):
        if view.visual.player_lines or view.visual.enemy_lines:
            player = " ".join(view.visual.player_lines) or view.player.display_name
            enemy = " ".join(view.visual.enemy_lines) or view.enemy.display_name
        else:
            player = f"[ {view.player.display_name} ]"
            enemy = f"[ {view.enemy.display_name} ]"
        return (self._fit(f"{player}   VS   {enemy}", width).center(width),)

    def _display_log_lines(self, view, width):
        lines = []
        for entry in view.log_entries:
            for semantic_line in self._log_lines(entry):
                lines.extend(self._wrap(semantic_line, width))
        return tuple(lines[-self.VISIBLE_LOG_LINES:] or ("Battle awaits.",))

    def _control_lines(self, view, width):
        if view.interaction_phase == InteractionPhase.ACTIONS:
            labels = tuple(
                f"[{self._ACTION_KEYS[option.intent]}] {option.label}"
                + (" [Unavailable]" if not option.enabled else "")
                for option in view.action_options
            )
            labels += ("[S] Super",)
            if width < 72:
                return (
                    "Actions",
                    *(line for label in labels for line in self._wrap(label, width)),
                )
            first_row = "   ".join(labels[:3])
            second_row = "   ".join(labels[3:])
            return (
                "Actions",
                *self._wrap(first_row, width),
                *self._wrap(second_row, width),
            )

        if view.interaction_phase in {
            InteractionPhase.INVENTORY,
            InteractionPhase.INVENTORY_ITEM,
            InteractionPhase.INVENTORY_INSPECT,
            InteractionPhase.INVENTORY_COMBINATION,
            InteractionPhase.INVENTORY_CONFIRMATION,
        }:
            return self._inventory_control_lines(view, width)

        lines = [self._phase_heading(view.interaction_phase)]
        for move in view.move_options:
            tags = " | ".join(move.tags)
            suffix = " [Unavailable]" if not move.enabled else ""
            lines.extend(
                self._wrap(
                    f"{move.number}. {move.name} [{tags}]{suffix}",
                    width,
                )
            )
            lines.extend(
                "   " + summary_line
                for summary_line in self._wrap(move.rules_summary, max(20, width - 3))
            )
        lines.append("0. Back")
        return tuple(lines)

    def _inventory_control_lines(self, view, width):
        if view.interaction_phase == InteractionPhase.INVENTORY:
            lines = ["Choose an item:"]
            lines.extend(
                line
                for option in view.inventory_items
                for line in self._wrap(
                    f"{option.number}. {option.display_name} x{option.quantity}",
                    width,
                )
            )
        elif view.interaction_phase == InteractionPhase.INVENTORY_ITEM:
            item = view.selected_inventory_item
            lines = [f"{item.display_name} x{item.quantity}", ""]
            for option in view.inventory_commands:
                suffix = " [Unavailable]" if not option.enabled else ""
                lines.extend(
                    self._wrap(f"{option.number}. {option.label}{suffix}", width)
                )
        elif view.interaction_phase == InteractionPhase.INVENTORY_INSPECT:
            inspection = view.inventory_inspection
            lines = [inspection.display_name, ""]
            lines.extend(self._wrap(inspection.description, width))
            lines.append("")
        elif view.interaction_phase == InteractionPhase.INVENTORY_COMBINATION:
            item = view.selected_inventory_item
            lines = [f"Use {item.display_name} with:", ""]
            lines.extend(
                line
                for option in view.inventory_companions
                for line in self._wrap(
                    f"{option.number}. {option.display_name} x{option.quantity}",
                    width,
                )
            )
        else:
            confirmation = view.inventory_confirmation
            lines = [
                (
                    f"Combine {confirmation.source_display_name} and "
                    f"{confirmation.companion_display_name}"
                ),
                f"to prepare {confirmation.result_display_name}?",
                "",
                "[Y] Yes",
                "[N] No",
            ]
        lines.append("0. Back")
        return tuple(lines)

    def _super_meter_line(self, view, width):
        meter = view.super_meter
        suffix = f" {meter.current}/{meter.maximum}"
        if meter.activation_offered:
            suffix += " READY"
        prefix = "SUPER "
        bar_width = max(8, width - len(prefix) - len(suffix) - 2)
        filled = bar_width * meter.fill_bps // 10_000
        if self._unicode_enabled:
            bar = "█" * filled + "░" * (bar_width - filled)
        else:
            bar = "#" * filled + "-" * (bar_width - filled)
        return self._fit(f"{prefix}[{bar}]{suffix}", width)

    def _frame_characters(self):
        if self._unicode_enabled:
            return {
                "top_left": "┌",
                "top_right": "┐",
                "bottom_left": "└",
                "bottom_right": "┘",
                "middle_left": "├",
                "middle_right": "┤",
                "horizontal": "─",
                "vertical": "│",
            }
        return {
            "top_left": "+",
            "top_right": "+",
            "bottom_left": "+",
            "bottom_right": "+",
            "middle_left": "+",
            "middle_right": "+",
            "horizontal": "-",
            "vertical": "|",
        }

    @staticmethod
    def _boxed_line(content, width, vertical):
        inner_width = width - 4
        return f"{vertical} {content[:inner_width].ljust(inner_width)} {vertical}"

    @staticmethod
    def _fit(value, width):
        if len(value) <= width:
            return value
        if width <= 3:
            return value[:width]
        return value[: width - 3] + "..."

    @staticmethod
    def _wrap(value, width):
        return tuple(
            textwrap.wrap(
                value,
                width=max(1, width),
                break_long_words=True,
                break_on_hyphens=False,
            )
            or ("",)
        )

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
        elif entry.event_type == BattleEventType.INVENTORY:
            if not entry.accepted:
                lines.append("That inventory action is not available.")
        elif entry.event_type == BattleEventType.STATUS:
            pass
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
        lines.extend(self._outcome_lines(entry))
        return tuple(lines)

    @staticmethod
    def _outcome_lines(entry):
        lines = []
        actor = entry.actor_name or "Combatant"
        target = entry.target_name or "target"
        for outcome in entry.outcomes:
            if outcome.outcome_type == CombatOutcomeType.OVERCHARGE_CONSUMED:
                lines.append(f"{actor} discharged Arcane Overcharge.")
            elif outcome.outcome_type == CombatOutcomeType.OVERCHARGE_GAINED:
                lines.append(f"{actor} gathered Arcane Overcharge.")
            elif outcome.outcome_type == CombatOutcomeType.BREAK_CLEARED:
                lines.append(f"{target}'s Gravemantle Break cleared.")
            elif outcome.outcome_type == CombatOutcomeType.BREAK_APPLIED:
                lines.append(f"{target}'s defenses were ruptured.")
            elif outcome.outcome_type == CombatOutcomeType.BACKLASH_DAMAGE:
                lines.append(f"{actor} suffered {outcome.amount} backlash damage.")
            elif outcome.outcome_type == CombatOutcomeType.INSTABILITY_CLEARED:
                lines.append(f"{actor}'s Arcane Instability cleared.")
            elif outcome.outcome_type == CombatOutcomeType.INSTABILITY_APPLIED:
                lines.append(f"{actor} became physically unstable.")
            elif outcome.outcome_type == CombatOutcomeType.COMPOUNDS_CONSUMED:
                if entry.action_name == "prepare_cinderwrit":
                    lines.append(f"{actor} combined Ember Shard with Deep Coal.")
                elif entry.action_name == "prepare_poison_infusion":
                    lines.append(f"{actor} combined Deep Coal with Night Berry.")
                else:
                    lines.append(f"{actor} combined Deep Coal with Ember Shard.")
            elif outcome.outcome_type == CombatOutcomeType.CINDERWRIT_PREPARED:
                lines.append("Cinderwrit Barb is ready.")
            elif outcome.outcome_type == CombatOutcomeType.FIRE_INFUSION_PREPARED:
                lines.append("A Fire-Infused Barb is ready.")
            elif outcome.outcome_type == CombatOutcomeType.POISON_INFUSION_PREPARED:
                lines.append("A Poison-Infused Barb is ready.")
            elif outcome.outcome_type == CombatOutcomeType.CINDERWRIT_CONSUMED:
                lines.append(f"{actor} loosed the prepared Cinderwrit Barb.")
            elif outcome.outcome_type == CombatOutcomeType.BURN_APPLIED:
                lines.append(f"{target} began burning.")
            elif outcome.outcome_type == CombatOutcomeType.BURN_REFRESHED:
                lines.append(f"{target}'s Burn was refreshed.")
            elif outcome.outcome_type == CombatOutcomeType.BURN_TICK:
                lines.append(f"{actor} suffered {outcome.amount} Burn damage.")
            elif outcome.outcome_type == CombatOutcomeType.BURN_EXPIRED:
                subject = (
                    actor
                    if outcome.target == CombatOutcomeTarget.ACTOR
                    else target
                )
                lines.append(f"{subject}'s Burn expired.")
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

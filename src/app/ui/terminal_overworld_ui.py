"""Stateless terminal rendering and semantic input for the overworld."""

import builtins
import shutil
import sys
import textwrap

from app.presentation.overworld_models import (
    MapNodeState,
    OverworldAction,
    OverworldAvailabilityReason,
    OverworldScreen,
    OverworldView,
)
from app.ui.overworld_ui import ChooseOverworldAction, ChooseOverworldItem


class TerminalOverworldUI:
    _REJECTED = object()
    _ACTION_KEYS = {
        OverworldAction.CHARACTER: "C",
        OverworldAction.ITEMS: "I",
        OverworldAction.MAP: "M",
        OverworldAction.OPTIONS: "O",
        OverworldAction.SKILLS: "S",
        OverworldAction.WEAPON: "W",
        OverworldAction.EQUIPMENT: "E",
        OverworldAction.CRAFT: "C",
        OverworldAction.INSPECT: "I",
        OverworldAction.USE: "U",
        OverworldAction.SAVE: "S",
        OverworldAction.LOAD: "L",
        OverworldAction.QUIT: "Q",
        OverworldAction.BACK: "B",
        OverworldAction.CONFIRM: "Y",
        OverworldAction.CANCEL: "N",
        OverworldAction.ENTER_ENCOUNTER: "E",
        OverworldAction.RETRY: "R",
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
            lambda: shutil.get_terminal_size((100, 30)).columns
        )
        self._unicode_enabled = bool(unicode_enabled)
        if interactive is None:
            interactive = sys.stdin.isatty() and sys.stdout.isatty()
        if ansi_enabled is None:
            ansi_enabled = interactive
        self._ansi_enabled = bool(ansi_enabled)
        self._interactive = bool(interactive)

    def render(self, view):
        if not isinstance(view, OverworldView):
            raise TypeError("view must be an OverworldView")
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
        if not isinstance(view, OverworldView):
            raise TypeError("view must be an OverworldView")
        while True:
            raw_value = self._input("> ")
            if not isinstance(raw_value, str):
                self._output("That option is not available.")
                continue
            choice = raw_value.strip().lower()
            selected = self._translate_choice(view, choice)
            if selected is self._REJECTED:
                continue
            if selected is not None:
                return selected
            self._output("That option is not available.")

    def _translate_choice(self, view, choice):
        if view.screen is OverworldScreen.ITEMS and view.inventory is not None:
            for number, item in enumerate(view.inventory.items, start=1):
                if choice in (str(number), item.display_name.lower()):
                    return ChooseOverworldItem(item.selection_key)

        numbered_options = view.screen not in {
            OverworldScreen.ITEMS,
            OverworldScreen.MAP,
            OverworldScreen.OPTIONS,
            OverworldScreen.QUIT_CONFIRMATION,
        }
        for number, option in enumerate(self._control_options(view), start=1):
            key = self._ACTION_KEYS[option.action].lower()
            aliases = {key, option.label.lower(), option.action.value}
            if numbered_options:
                aliases.add(str(number))
            if option.action is OverworldAction.BACK:
                aliases.add("0")
            if choice not in aliases:
                continue
            if option.enabled:
                return ChooseOverworldAction(option.action)
            self._output(self._disabled_message(option.disabled_reason))
            return self._REJECTED
        return None

    def _framed_lines(self, view, width):
        chars = self._frame_characters()
        inner_width = width - 4
        lines = [
            chars["top_left"]
            + chars["horizontal"] * (width - 2)
            + chars["top_right"]
        ]
        title = self._screen_title(view.screen)
        lines.append(self._boxed_line(f"{title}  |  {view.location_label}", width, chars))
        lines.append(self._divider(width, chars))
        for body_line in self._body_lines(view, inner_width):
            lines.append(self._boxed_line(body_line, width, chars))
        lines.append(self._divider(width, chars))
        for control_line in self._control_lines(view, inner_width):
            lines.append(self._boxed_line(control_line, width, chars))
        lines.append(
            chars["bottom_left"]
            + chars["horizontal"] * (width - 2)
            + chars["bottom_right"]
        )
        return tuple(lines)

    def _linear_lines(self, view, width):
        lines = [
            self._screen_title(view.screen),
            f"Location: {view.location_label}",
            "",
        ]
        lines.extend(self._body_lines(view, width))
        lines.append("")
        lines.extend(self._control_lines(view, width))
        return tuple(
            wrapped
            for line in lines
            for wrapped in self._wrap(line, width)
        )

    def _body_lines(self, view, width):
        if view.screen in {
            OverworldScreen.MAIN,
            OverworldScreen.OPTIONS,
            OverworldScreen.QUIT_CONFIRMATION,
        }:
            lines = ["ADVENTURE", ""]
            lines.extend(self._wrapped(view.adventure_text, width))
            if view.screen is OverworldScreen.QUIT_CONFIRMATION:
                lines.extend(("", "Exit this session without saving?"))
        elif view.screen is OverworldScreen.CHARACTER:
            lines = list(self._character_lines(view, width))
        elif view.screen is OverworldScreen.SKILLS:
            lines = list(self._skills_lines(view, width))
        elif view.screen is OverworldScreen.WEAPON:
            lines = list(self._weapon_lines(view, width))
        elif view.screen is OverworldScreen.EQUIPMENT:
            lines = list(self._equipment_lines(view))
        elif view.screen in {OverworldScreen.ITEMS, OverworldScreen.ITEM_INSPECT}:
            lines = list(self._inventory_lines(view, width))
        elif view.screen is OverworldScreen.MAP:
            lines = list(self._map_lines(view, width))
        else:
            raise ValueError(f"unsupported overworld screen: {view.screen!r}")
        if view.notice:
            lines.extend(("", f"NOTICE: {view.notice}"))
        return tuple(lines or ("",))

    def _character_lines(self, view, width):
        character = view.character
        lines = [
            f"[ {character.display_name} ]",
            character.archetype_label,
            "",
            "STATS",
        ]
        stat_pairs = [
            f"{row.label}: {row.value}"
            for row in character.stats
        ]
        lines.extend(self._two_column_values(stat_pairs, width))
        lines.extend(
            (
                "",
                f"Level {character.level}",
                f"HP {character.hp_current}/{character.hp_maximum}",
                f"Mana {character.mana_current}/{character.mana_maximum}",
                f"Super {character.super_current}/{character.super_maximum}",
                self._meter_line(
                    "XP",
                    character.exp_current,
                    character.exp_threshold,
                    character.exp_fill_bps,
                    width,
                ),
            )
        )
        return tuple(lines)

    def _skills_lines(self, view, width):
        skills = view.skills
        lines = ["LEVEL UP", "Growth Points: Unavailable", skills.growth_message, ""]
        for row in skills.stats:
            lines.append(f"{row.label:<14} {row.value:>3}  [+ Unavailable]")
        lines.extend(("", "ATTACKS"))
        lines.extend(move.name for move in skills.moves)
        return tuple(lines)

    def _weapon_lines(self, view, width):
        weapon = view.weapon
        lines = [
            weapon.name,
            weapon.weapon_type,
            f"Wielder: {weapon.intended_wielder}",
            "",
            "BONUSES",
        ]
        lines.extend(f"{bonus.label} +{bonus.amount}" for bonus in weapon.bonuses)
        lines.extend(("", "DESCRIPTION"))
        lines.extend(self._wrapped(weapon.description, width))
        return tuple(lines)

    @staticmethod
    def _equipment_lines(view):
        equipment = view.equipment
        return (
            "ACCESSORIES",
            "",
            f"[ Necklace ]  {equipment.necklace.item_name}",
            f"[ Ring     ]  {equipment.ring.item_name}",
            "",
            "BENEFITS",
            *equipment.benefits,
        )

    def _inventory_lines(self, view, width):
        inventory = view.inventory
        if view.screen is OverworldScreen.ITEM_INSPECT:
            item = inventory.inspected_item
            lines = [item.display_name, f"Quantity: {item.quantity}", ""]
            lines.extend(self._wrapped(item.description, width))
            return tuple(lines)
        lines = ["ITEMS", ""]
        if not inventory.items:
            lines.append("Your persistent inventory is empty.")
            return tuple(lines)
        for number, item in enumerate(inventory.items, start=1):
            marker = ">" if item.selection_key == inventory.selected_item_key else " "
            lines.append(f"{marker} {number}. {item.display_name} x{item.quantity}")
        return tuple(lines)

    def _map_lines(self, view, width):
        lines = ["SURFACE ROUTE", ""]
        markers = {
            MapNodeState.CURRENT: ">>",
            MapNodeState.COMPLETED: "OK",
            MapNodeState.REMAINING: "..",
        }
        for index, node in enumerate(view.route_map.nodes):
            lines.append(
                f"{markers[node.state]} [{node.kind_label}] {node.display_label}"
            )
            if index < len(view.route_map.nodes) - 1:
                lines.append("   |")
        lines.extend(("", "Travel is fixed; the map is inspection-only."))
        return tuple(self._fit(line, width) for line in lines)

    def _control_lines(self, view, width):
        labels = []
        for number, option in enumerate(self._control_options(view), start=1):
            key = self._ACTION_KEYS[option.action]
            prefix = f"[{key}]"
            if view.screen not in {
                OverworldScreen.ITEMS,
                OverworldScreen.MAP,
                OverworldScreen.OPTIONS,
                OverworldScreen.QUIT_CONFIRMATION,
            }:
                prefix = f"[{number}/{key}]"
            suffix = " [Unavailable]" if not option.enabled else ""
            labels.append(f"{prefix} {option.label}{suffix}")
        if not labels:
            return ("",)
        return self._two_column_values(labels, width)

    @staticmethod
    def _control_options(view):
        if view.contextual_route_option is None:
            return view.options
        return (*view.options, view.contextual_route_option)

    @staticmethod
    def _two_column_values(values, width):
        column_width = max(1, (width - 3) // 2)
        rows = []
        for index in range(0, len(values), 2):
            left = values[index][:column_width]
            right = values[index + 1] if index + 1 < len(values) else ""
            rows.append(left.ljust(column_width) + " | " + right[:column_width])
        return tuple(rows)

    def _meter_line(self, label, current, maximum, fill_bps, width):
        suffix = f" {current}/{maximum}"
        bar_width = max(8, width - len(label) - len(suffix) - 4)
        filled = bar_width * fill_bps // 10_000
        if self._unicode_enabled:
            bar = "█" * filled + "░" * (bar_width - filled)
        else:
            bar = "#" * filled + "-" * (bar_width - filled)
        return self._fit(f"{label} [{bar}]{suffix}", width)

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
    def _divider(width, chars):
        return (
            chars["middle_left"]
            + chars["horizontal"] * (width - 2)
            + chars["middle_right"]
        )

    @staticmethod
    def _boxed_line(content, width, chars):
        inner_width = width - 4
        return (
            f"{chars['vertical']} "
            f"{content[:inner_width].ljust(inner_width)} "
            f"{chars['vertical']}"
        )

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

    def _wrapped(self, value, width):
        return self._wrap(value, width)

    @staticmethod
    def _screen_title(screen):
        return {
            OverworldScreen.MAIN: "OVERWORLD",
            OverworldScreen.CHARACTER: "CHARACTER",
            OverworldScreen.SKILLS: "SKILLS",
            OverworldScreen.WEAPON: "WEAPON",
            OverworldScreen.EQUIPMENT: "EQUIPMENT",
            OverworldScreen.ITEMS: "ITEMS",
            OverworldScreen.ITEM_INSPECT: "ITEM INSPECTION",
            OverworldScreen.MAP: "MAP",
            OverworldScreen.OPTIONS: "OPTIONS",
            OverworldScreen.QUIT_CONFIRMATION: "QUIT",
        }[screen]

    @staticmethod
    def _disabled_message(reason):
        return {
            OverworldAvailabilityReason.GROWTH_UNAVAILABLE: (
                "Growth Point spending is not yet available."
            ),
            OverworldAvailabilityReason.CRAFT_UNAVAILABLE: (
                "Crafting is not yet available."
            ),
            OverworldAvailabilityReason.NO_ITEM_SELECTED: (
                "Select an item first."
            ),
            OverworldAvailabilityReason.NO_OVERWORLD_USE: (
                "That item cannot be used from the overworld."
            ),
            OverworldAvailabilityReason.ENCOUNTER_INSPECTION_UNAVAILABLE: (
                "Encounter inspection is not yet available."
            ),
            OverworldAvailabilityReason.SAVE_UNAVAILABLE: (
                "Saving is not yet available."
            ),
            OverworldAvailabilityReason.LOAD_UNAVAILABLE: (
                "Loading is not yet available."
            ),
        }[reason]

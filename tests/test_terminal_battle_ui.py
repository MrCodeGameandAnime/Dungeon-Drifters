from dataclasses import replace

from app.presentation.battle_models import (
    ActionAvailabilityReason,
    ActionIntent,
    ActionOptionView,
    BattleEventType,
    BattleLogEntry,
    BattleView,
    CombatantView,
    InteractionPhase,
    InventoryActionOptionView,
    InventoryAvailabilityReason,
    InventoryIngredientView,
    MoveAvailabilityReason,
    MoveOptionView,
    SuperMeterView,
)
from app.combat.result import CombatOutcome, CombatOutcomeTarget, CombatOutcomeType
from app.ui.battle_ui import ChooseAction, ChooseInventoryAction, ChooseMove, GoBack
from app.ui.terminal_battle_ui import TerminalBattleUI


class TerminalHarness:
    def __init__(self, inputs=()):
        self.inputs = iter(inputs)
        self.lines = []

    def input(self, prompt):
        self.lines.append(prompt)
        return next(self.inputs)

    def output(self, message):
        self.lines.append(message)


def _view(
    *,
    phase=InteractionPhase.ACTIONS,
    super_ready=False,
    action_options=None,
    move_options=(),
    inventory_options=(),
    log_entries=(),
):
    player = CombatantView("Ser Branoc", 116, 116, 46, 46, 0, 100)
    enemy = CombatantView("Goblin", 60, 60)
    actions = action_options or (
        ActionOptionView(ActionIntent.ATTACK, 1, "Attack", True),
        ActionOptionView(ActionIntent.DEFEND, 2, "Defend", True),
        ActionOptionView(
            ActionIntent.HEAL,
            3,
            "Heal",
            False,
            ActionAvailabilityReason.NO_HEALING_MOVES,
        ),
        ActionOptionView(
            ActionIntent.ITEMS,
            4,
            "Items",
            False,
            ActionAvailabilityReason.NOT_IMPLEMENTED,
        ),
        ActionOptionView(
            ActionIntent.ESCAPE,
            5,
            "Escape",
            False,
            ActionAvailabilityReason.NOT_IMPLEMENTED,
        ),
    )
    return BattleView(
        interaction_phase=phase,
        player=player,
        enemy=enemy,
        super_meter=SuperMeterView(
            current=100 if super_ready else 0,
            maximum=100,
            fill_bps=10_000 if super_ready else 0,
            ready=super_ready,
            activation_key="S",
            activation_offered=super_ready,
        ),
        action_options=actions,
        move_options=move_options,
        inventory_options=inventory_options,
        log_entries=log_entries,
    )


def _ui(inputs):
    harness = TerminalHarness(inputs)
    return TerminalBattleUI(
        input_func=harness.input,
        output_func=harness.output,
        width_provider=lambda: 80,
        ansi_enabled=False,
        interactive=False,
    ), harness


def _contains(harness, text):
    return any(text in line for line in harness.lines)


def test_action_numbers_and_aliases_return_semantic_actions():
    for raw, expected in (("1", ActionIntent.ATTACK), ("defend", ActionIntent.DEFEND)):
        ui, _ = _ui((raw,))
        assert ui.read_input(_view()) == ChooseAction(expected)


def test_mnemonic_action_bindings_are_case_insensitive():
    actions = tuple(
        ActionOptionView(intent, number, intent.name.title(), True)
        for intent, number in (
            (ActionIntent.ATTACK, 1),
            (ActionIntent.DEFEND, 2),
            (ActionIntent.HEAL, 3),
            (ActionIntent.ITEMS, 4),
            (ActionIntent.ESCAPE, 5),
        )
    )
    for lower, upper, intent in (
        ("a", "A", ActionIntent.ATTACK),
        ("d", "D", ActionIntent.DEFEND),
        ("h", "H", ActionIntent.HEAL),
        ("i", "I", ActionIntent.ITEMS),
        ("e", "E", ActionIntent.ESCAPE),
    ):
        for raw in (lower, upper):
            ui, _ = _ui((raw,))
            assert ui.read_input(_view(action_options=actions)) == ChooseAction(intent)


def test_super_key_maps_to_semantic_action_from_any_phase():
    ui, _ = _ui(("S",))

    result = ui.read_input(
        _view(phase=InteractionPhase.REGULAR_MOVES, super_ready=True)
    )

    assert result == ChooseAction(ActionIntent.SUPER)


def test_unready_super_reports_not_ready_and_reprompts_without_semantic_action():
    ui, harness = _ui(("s", "a"))

    assert ui.read_input(_view()) == ChooseAction(ActionIntent.ATTACK)
    assert "Super is not ready." in harness.lines


def test_move_number_maps_to_opaque_offered_key():
    move = MoveOptionView(
        "Ironwake Dismemberment",
        4,
        "Ironwake Dismemberment",
        ("Heavy",),
        "A crushing strike.",
        None,
        True,
    )
    ui, _ = _ui(("4",))

    assert ui.read_input(
        _view(phase=InteractionPhase.REGULAR_MOVES, move_options=(move,))
    ) == ChooseMove("Ironwake Dismemberment")


def test_inventory_phase_renders_counts_and_translates_only_enabled_actions():
    ingredient = InventoryIngredientView("ember_shard", "Ember Shard", 1, 1)
    action = InventoryActionOptionView(
        "prepare_cinderwrit",
        1,
        "Prepare Cinderwrit Barb",
        (ingredient,),
        True,
    )
    view = _view(
        phase=InteractionPhase.INVENTORY,
        inventory_options=(action,),
    )
    ui, harness = _ui(("1",))

    ui.render(view)

    assert ui.read_input(view) == ChooseInventoryAction("prepare_cinderwrit")
    assert _contains(harness, "Choose an inventory action:")
    assert _contains(harness, "Prepare Cinderwrit Barb")
    assert _contains(harness, "Ember Shard 1/1")


def test_disabled_inventory_action_reprompts_and_back_remains_semantic():
    action = InventoryActionOptionView(
        "prepare_cinderwrit",
        1,
        "Prepare Cinderwrit Barb",
        (InventoryIngredientView("ember_shard", "Ember Shard", 1, 1),),
        False,
        InventoryAvailabilityReason.NOT_IMPLEMENTED,
    )
    view = _view(
        phase=InteractionPhase.INVENTORY,
        inventory_options=(action,),
    )
    ui, harness = _ui(("1", "0"))

    assert ui.read_input(view) == GoBack()
    assert "Prepare Cinderwrit Barb is not available." in harness.lines


def test_back_is_returned_only_from_move_selection_phase():
    ui, harness = _ui(("0", "attack"))

    assert ui.read_input(_view()) == ChooseAction(ActionIntent.ATTACK)
    assert "That is not a valid move. Please try again." in harness.lines

    ui, _ = _ui(("0",))
    assert isinstance(
        ui.read_input(_view(phase=InteractionPhase.REGULAR_MOVES)),
        GoBack,
    )


def test_malformed_and_disabled_choices_reprompt_locally():
    ui, harness = _ui(("nonsense", "3", "2"))

    assert ui.read_input(_view()) == ChooseAction(ActionIntent.DEFEND)
    assert "Heal is not available." in harness.lines
    assert harness.lines.count("That is not a valid move. Please try again.") == 2


def test_disabled_move_is_not_returned():
    disabled = MoveOptionView(
        "Brace",
        1,
        "Brace",
        ("Utility", "5 Mana"),
        "Brace.",
        "5 Mana",
        False,
        MoveAvailabilityReason.INSUFFICIENT_RESOURCE,
    )
    enabled = MoveOptionView(
        "Crestgrave Reaping",
        2,
        "Crestgrave Reaping",
        ("Normal",),
        "Strike.",
        None,
        True,
    )
    ui, harness = _ui(("1", "2"))

    result = ui.read_input(
        _view(
            phase=InteractionPhase.REGULAR_MOVES,
            move_options=(disabled, enabled),
        )
    )

    assert result == ChooseMove("Crestgrave Reaping")
    assert "Brace is not available." in harness.lines


def test_render_uses_injected_output_and_semantic_log_values():
    entry = BattleLogEntry(
        event_type=BattleEventType.DAMAGE,
        actor_name="Ser Branoc",
        target_name="Goblin",
        action_name="Ironwake Dismemberment",
        accepted=True,
        hit=True,
        amount=21,
        critical=True,
    )
    ui, harness = _ui(())

    ui.render(_view(log_entries=(entry,)))

    assert _contains(harness, "Ser Branoc")
    assert _contains(harness, "HP 116/116")
    assert _contains(harness, "Goblin")
    assert _contains(harness, "HP 60/60")
    assert _contains(
        harness,
        "Ser Branoc used Ironwake Dismemberment. Critical hit! It dealt 21 damage.",
    )
    assert _contains(harness, "Actions")


def test_complex_gravemantle_log_keeps_primary_result_and_ordered_outcomes():
    outcomes = (
        CombatOutcome(CombatOutcomeType.OVERCHARGE_CONSUMED),
        CombatOutcome(CombatOutcomeType.BREAK_CLEARED),
        CombatOutcome(
            CombatOutcomeType.INSTABILITY_CLEARED,
            target=CombatOutcomeTarget.ACTOR,
        ),
        CombatOutcome(CombatOutcomeType.BREAK_APPLIED),
        CombatOutcome(CombatOutcomeType.OVERCHARGE_GAINED),
        CombatOutcome(
            CombatOutcomeType.BACKLASH_DAMAGE,
            amount=8,
            target=CombatOutcomeTarget.ACTOR,
        ),
        CombatOutcome(
            CombatOutcomeType.INSTABILITY_APPLIED,
            target=CombatOutcomeTarget.ACTOR,
        ),
    )
    primary = BattleLogEntry(
        event_type=BattleEventType.DAMAGE,
        actor_name="Azhvielle",
        target_name="Goblin",
        action_name="Gravemantle Rupture",
        accepted=True,
        hit=True,
        amount=20,
        resource_spent=12,
        outcomes=outcomes,
    )
    enemy_response = BattleLogEntry(
        event_type=BattleEventType.MISS,
        actor_name="Goblin",
        action_name="slash",
        accepted=True,
        hit=False,
    )
    ui, harness = _ui(())

    ui.render(_view(log_entries=(primary, enemy_response)))
    text = "\n".join(harness.lines)

    assert "Azhvielle used Gravemantle Rupture. It dealt 20 damage." in text
    assert "Resource spent: 12." in text
    assert "Azhvielle discharged Arcane Overcharge." in text
    assert "Goblin's Gravemantle Break cleared." in text
    assert "Azhvielle's Arcane Instability cleared." in text
    assert "Goblin's defenses were ruptured." in text
    assert "Azhvielle gathered Arcane Overcharge." in text
    assert "Azhvielle suffered 8 backlash damage." in text
    assert "Azhvielle became physically unstable." in text
    assert "Goblin used slash, but missed." in text


def test_complex_log_remains_width_safe_at_narrow_terminal_width():
    entry = BattleLogEntry(
        event_type=BattleEventType.DAMAGE,
        actor_name="Azhvielle",
        target_name="Goblin",
        action_name="Gravemantle Rupture",
        accepted=True,
        hit=True,
        amount=20,
        outcomes=(
            CombatOutcome(
                CombatOutcomeType.BACKLASH_DAMAGE,
                amount=8,
                target=CombatOutcomeTarget.ACTOR,
            ),
        ),
    )
    harness = TerminalHarness()
    ui = TerminalBattleUI(
        input_func=harness.input,
        output_func=harness.output,
        width_provider=lambda: 60,
        ansi_enabled=False,
        interactive=False,
    )

    ui.render(_view(log_entries=(entry,)))

    assert all(len(line) <= 60 for line in harness.lines)


def test_structured_move_menu_uses_readable_tags_and_wrapped_summaries():
    moves = (
        MoveOptionView(
            "Crestgrave Reaping",
            1,
            "Crestgrave Reaping",
            ("Normal",),
            "Sunder-Spire tears through the target.",
            None,
            True,
        ),
        MoveOptionView(
            "Cinderlung Vesper",
            2,
            "Cinderlung Vesper",
            ("Fire Magic", "3 Mana"),
            "A black war-breath erupts forward.",
            "3 Mana",
            True,
        ),
        MoveOptionView(
            "Brace",
            3,
            "Brace",
            ("Utility", "5 Mana"),
            (
                "Brace against the next enemy action, reducing physical damage "
                "by 40%, and empower your next Heavy attack by 30%."
            ),
            "5 Mana",
            True,
        ),
        MoveOptionView(
            "Ironwake Dismemberment",
            4,
            "Ironwake Dismemberment",
            ("Heavy", "Empowered +30%"),
            "A crushing Sunder-Spire strike.",
            None,
            True,
        ),
    )
    harness = TerminalHarness()
    ui = TerminalBattleUI(
        input_func=harness.input,
        output_func=harness.output,
        width_provider=lambda: 60,
        ansi_enabled=False,
        interactive=False,
    )

    ui.render(
        _view(
            phase=InteractionPhase.REGULAR_MOVES,
            move_options=moves,
        )
    )

    assert _contains(harness, "1. Crestgrave Reaping [Normal]")
    assert _contains(harness, "2. Cinderlung Vesper [Fire Magic | 3 Mana]")
    assert _contains(harness, "3. Brace [Utility | 5 Mana]")
    assert _contains(
        harness,
        "4. Ironwake Dismemberment [Heavy | Empowered +30%]",
    )
    assert not any("[none 0]" in line for line in harness.lines)
    assert all(
        len(line) <= 60
        for line in harness.lines
    )
    assert _contains(harness, "Brace against")
    assert _contains(harness, "0. Back")


def test_back_is_rendered_only_during_move_phases_and_super_is_separate():
    ui, actions = _ui(())
    ui.render(_view())

    assert not _contains(actions, "0. Back")
    assert not _contains(actions, "6. Super")

    super_move = MoveOptionView(
        "Third Gate Obsequy",
        1,
        "Third Gate Obsequy",
        ("Super", "100 Super"),
        "A forbidden gate manifests.",
        "100 Super",
        True,
    )
    ui, super_menu = _ui(())
    ui.render(
        _view(
            phase=InteractionPhase.SUPER_MOVES,
            super_ready=True,
            move_options=(super_move,),
        )
    )

    assert _contains(super_menu, "Choose a Super:")
    assert _contains(super_menu, "1. Third Gate Obsequy [Super | 100 Super]")
    assert _contains(super_menu, "0. Back")


def test_render_preserves_all_existing_move_result_categories_and_details():
    entries = (
        BattleLogEntry(
            BattleEventType.DAMAGE,
            actor_name="Ser Branoc",
            action_name="Cut",
            accepted=True,
            hit=True,
            amount=7,
        ),
        BattleLogEntry(
            BattleEventType.HEALING,
            actor_name="Ser Branoc",
            action_name="Recover",
            accepted=True,
            hit=True,
            amount=3,
        ),
        BattleLogEntry(
            BattleEventType.MISS,
            actor_name="Goblin",
            action_name="Whiff",
            accepted=True,
            hit=False,
        ),
        BattleLogEntry(
            BattleEventType.ACTION_REJECTED,
            actor_name="Ser Branoc",
            action_name="Blocked",
            accepted=False,
            hit=False,
            reason="rejected",
        ),
        BattleLogEntry(
            BattleEventType.UTILITY,
            actor_name="Ser Branoc",
            action_name="Brace",
            accepted=True,
            hit=True,
            resource_spent=5,
            statuses_applied=("ward",),
        ),
        BattleLogEntry(
            BattleEventType.DEFEND,
            actor_name="Ser Branoc",
            action_name="Defend",
            accepted=True,
            hit=False,
        ),
    )
    ui, _ = _ui(())

    rendered_lines = tuple(
        line
        for entry in entries
        for line in ui._log_lines(entry)
    )

    assert "Ser Branoc used Cut. It dealt 7 damage." in rendered_lines
    assert "Ser Branoc used Recover. It restored 3 health." in rendered_lines
    assert "Goblin used Whiff, but missed." in rendered_lines
    assert "Ser Branoc used Blocked, but it failed: rejected." in rendered_lines
    assert "Ser Branoc used Brace. It resolved." in rendered_lines
    assert "Resource spent: 5." in rendered_lines
    assert "Statuses applied: ward." in rendered_lines
    assert "Ser Branoc used Defend." in rendered_lines


def test_persistent_hud_preserves_sections_and_width_at_supported_sizes():
    base_view = _view(
        log_entries=(
            BattleLogEntry(
                BattleEventType.DAMAGE,
                actor_name="Ser Branoc",
                target_name="Goblin",
                action_name="Crestgrave Reaping",
                accepted=True,
                hit=True,
                amount=10,
            ),
            BattleLogEntry(
                BattleEventType.MISS,
                actor_name="Goblin",
                action_name="slash",
                accepted=True,
                hit=False,
            ),
        ),
    )
    base_view = replace(
        base_view,
        player=replace(
            base_view.player,
            temporary_labels=("Defending", "Brace"),
            defending=True,
        ),
        enemy=CombatantView("Goblin", 40, 60, 3, 5, 20, 100),
    )

    for width in (120, 80, 60):
        harness = TerminalHarness()
        ui = TerminalBattleUI(
            input_func=harness.input,
            output_func=harness.output,
            width_provider=lambda width=width: width,
            ansi_enabled=False,
            interactive=False,
        )

        ui.render(base_view)
        text = "\n".join(harness.lines)

        assert all(len(line) <= width for line in harness.lines)
        assert "Ser Branoc" in text and "Goblin" in text
        assert "HP 116/116" in text and "HP 40/60" in text
        assert "Mana 46/46" in text and "Mana 3/5" in text
        assert "Super 20/100" in text
        assert "State: Defending, Brace" in text
        assert "VS" in text
        assert text.index("Crestgrave Reaping") < text.index("Goblin used slash")
        assert "[A] Attack" in text
        assert "[D] Defend" in text
        assert "[H]" in text and "Heal" in text
        assert "[I]" in text and "Items" in text
        assert "[E]" in text and "Escape" in text
        assert text.count("[Unavailable]") >= 3
        assert "[S] Super" in text
        assert "1. Attack" not in text
        assert "SUPER [" in text and "0/100" in text
        assert "\033[" not in text


def test_ascii_and_linear_fallback_preserve_meaning_without_ansi():
    harness = TerminalHarness()
    ui = TerminalBattleUI(
        input_func=harness.input,
        output_func=harness.output,
        width_provider=lambda: 50,
        unicode_enabled=False,
        ansi_enabled=False,
        interactive=False,
    )

    ui.render(_view())
    text = "\n".join(harness.lines)

    assert all(len(line) <= 50 for line in harness.lines)
    assert "STATUS" in text
    assert "Ser Branoc" in text and "Goblin" in text
    assert "ACTIONS" in text
    assert "SUPER [" in text
    assert "#" not in text
    assert "-" in text
    assert not any(character in text for character in "┌┐└┘├┤│─█░")
    assert "\033[" not in text


def test_super_meter_is_persistent_and_ready_text_matches_availability():
    ui, normal = _ui(())
    ui.render(_view())
    normal_text = "\n".join(normal.lines)

    assert "SUPER [" in normal_text
    assert "0/100" in normal_text
    assert "READY" not in normal_text

    ui, ready = _ui(())
    ui.render(_view(super_ready=True))
    ready_text = "\n".join(ready.lines)

    assert "SUPER [" in ready_text
    assert "100/100 READY" in ready_text
    assert "[S] Super" in ready_text


def test_interactive_ansi_mode_refreshes_without_retaining_state():
    harness = TerminalHarness()
    ui = TerminalBattleUI(
        input_func=harness.input,
        output_func=harness.output,
        width_provider=lambda: 80,
        ansi_enabled=True,
        interactive=True,
    )

    ui.render(_view())

    assert harness.lines[0].startswith("\033[2J\033[H")
    assert sum("\033[2J\033[H" in line for line in harness.lines) == 1


def test_adapter_retains_no_log_or_view_state_and_does_not_mutate_view():
    ui, _ = _ui(())
    view = _view()
    before = repr(view)

    ui.render(view)

    assert repr(view) == before
    assert set(vars(ui)) == {
        "_input",
        "_output",
        "_width_provider",
        "_unicode_enabled",
        "_ansi_enabled",
        "_interactive",
    }

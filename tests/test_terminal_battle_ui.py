from dataclasses import replace

from app.presentation.battle_models import (
    ActionAvailabilityReason,
    ActionIntent,
    ActionOptionView,
    BattleEventType,
    BattleLogEntry,
    BattleView,
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
from app.combat.result import CombatOutcome, CombatOutcomeTarget, CombatOutcomeType
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
    inventory_items=(),
    selected_inventory_item=None,
    inventory_commands=(),
    inventory_inspection=None,
    inventory_companions=(),
    inventory_confirmation=None,
    log_entries=(),
):
    player = CombatantView("Ser Branoc", 116, 116, 46, 46, 0, 100)
    enemy = EnemyCombatantView("enemy_1", "Goblin", 60, 60)
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
        enemies=(enemy,),
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
        inventory_items=inventory_items,
        selected_inventory_item=selected_inventory_item,
        inventory_commands=inventory_commands,
        inventory_inspection=inventory_inspection,
        inventory_companions=inventory_companions,
        inventory_confirmation=inventory_confirmation,
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


def test_inventory_phase_renders_owned_items_and_translates_stable_item_ids():
    item = InventoryItemOptionView("ember_shard", 1, "Ember Shard", 1, True)
    view = _view(
        phase=InteractionPhase.INVENTORY,
        inventory_items=(item,),
    )
    ui, harness = _ui(("1",))

    ui.render(view)

    assert ui.read_input(view) == ChooseInventoryItem("ember_shard")
    assert _contains(harness, "Choose an item:")
    assert _contains(harness, "Ember Shard x1")
    assert not _contains(harness, "Prepare Fire-Infused Barb")


def test_empty_inventory_renders_real_empty_state_and_back():
    ui, harness = _ui(("0",))
    view = _view(phase=InteractionPhase.INVENTORY, inventory_items=())

    ui.render(view)

    assert ui.read_input(view) == GoBack()
    assert _contains(harness, "Inventory")
    assert _contains(harness, "Your inventory is empty.")
    assert _contains(harness, "0. Back")


def test_item_commands_inspection_and_companion_selection_are_semantic():
    item = InventoryItemOptionView("ember_shard", 1, "Ember Shard", 1, True)
    commands = (
        InventoryCommandOptionView(InventoryCommand.INSPECT, 1, "Inspect", True),
        InventoryCommandOptionView(InventoryCommand.USE, 2, "Use", True),
    )
    command_view = _view(
        phase=InteractionPhase.INVENTORY_ITEM,
        selected_inventory_item=item,
        inventory_commands=commands,
    )
    ui, harness = _ui(("2",))

    ui.render(command_view)

    assert ui.read_input(command_view) == ChooseInventoryCommand(InventoryCommand.USE)
    assert _contains(harness, "Ember Shard x1")
    assert _contains(harness, "1. Inspect")
    assert _contains(harness, "2. Use")

    inspection_view = _view(
        phase=InteractionPhase.INVENTORY_INSPECT,
        selected_inventory_item=item,
        inventory_inspection=InventoryInspectionView(
            "ember_shard",
            "Ember Shard",
            "A heat-bearing mineral used to empower weapons with fire.",
        ),
    )
    inspection_ui, inspection_harness = _ui(("0",))
    inspection_ui.render(inspection_view)
    assert inspection_ui.read_input(inspection_view) == GoBack()
    assert _contains(inspection_harness, "A heat-bearing mineral")

    companion = InventoryItemOptionView("deep_coal", 1, "Deep Coal", 1, True)
    combination_view = _view(
        phase=InteractionPhase.INVENTORY_COMBINATION,
        selected_inventory_item=item,
        inventory_companions=(companion,),
    )
    companion_ui, companion_harness = _ui(("1",))
    companion_ui.render(combination_view)
    assert companion_ui.read_input(combination_view) == ChooseInventoryCompanion(
        "deep_coal"
    )
    assert _contains(companion_harness, "Use Ember Shard with:")
    assert _contains(companion_harness, "Deep Coal x1")


def test_inventory_confirmation_renders_and_translates_yes_no_and_back():
    confirmation = InventoryConfirmationView(
        "ember_shard",
        "Ember Shard",
        "deep_coal",
        "Deep Coal",
        "prepare_fire_infusion",
        "Fire-Infused Barb",
    )
    view = _view(
        phase=InteractionPhase.INVENTORY_CONFIRMATION,
        inventory_confirmation=confirmation,
    )
    ui, harness = _ui(("y",))
    ui.render(view)

    assert ui.read_input(view) == ConfirmInventoryUse(True)
    assert _contains(harness, "Combine Ember Shard and Deep Coal")
    assert _contains(harness, "to prepare Fire-Infused Barb?")
    assert _ui(("n",))[0].read_input(view) == ConfirmInventoryUse(False)
    assert _ui(("0",))[0].read_input(view) == GoBack()


def test_disabled_inventory_command_reprompts_and_back_remains_semantic():
    item = InventoryItemOptionView("ember_shard", 1, "Ember Shard", 1, True)
    command = InventoryCommandOptionView(
        InventoryCommand.USE,
        2,
        "Use",
        False,
        InventoryAvailabilityReason.MISSING_COMPANION,
    )
    view = _view(
        phase=InteractionPhase.INVENTORY_ITEM,
        selected_inventory_item=item,
        inventory_commands=(command,),
    )
    ui, harness = _ui(("2", "0"))

    assert ui.read_input(view) == GoBack()
    assert "Use is not available." in harness.lines


def test_preparation_outcomes_render_in_completed_mutation_order():
    entry = BattleLogEntry(
        event_type=BattleEventType.INVENTORY,
        actor_name="Zhaivra",
        action_name="prepare_fire_infusion",
        accepted=True,
        outcomes=(
            CombatOutcome(
                CombatOutcomeType.COMPOUNDS_CONSUMED,
                target=CombatOutcomeTarget.ACTOR,
            ),
            CombatOutcome(
                CombatOutcomeType.FIRE_INFUSION_PREPARED,
                target=CombatOutcomeTarget.ACTOR,
            ),
        ),
    )
    ui, harness = _ui(())

    ui.render(_view(log_entries=(entry,)))

    compound_line = next(
        index
        for index, line in enumerate(harness.lines)
        if "Zhaivra combined Ember Shard with Deep Coal." in line
    )
    prepared_line = next(
        index
        for index, line in enumerate(harness.lines)
        if "Fire-Infused Barb is ready." in line
    )
    assert compound_line < prepared_line


def test_burn_lifecycle_outcomes_render_as_status_damage_then_expiration():
    entry = BattleLogEntry(
        event_type=BattleEventType.STATUS,
        actor_name="Goblin",
        outcomes=(
            CombatOutcome(
                CombatOutcomeType.BURN_TICK,
                amount=6,
                target=CombatOutcomeTarget.ACTOR,
            ),
            CombatOutcome(
                CombatOutcomeType.BURN_EXPIRED,
                target=CombatOutcomeTarget.ACTOR,
            ),
        ),
    )
    ui, _ = _ui(())

    lines = ui._log_lines(entry)

    assert lines == (
        "Goblin suffered 6 Burn damage.",
        "Goblin's Burn expired.",
    )


def test_burn_application_and_refresh_render_against_exact_target():
    entry = BattleLogEntry(
        event_type=BattleEventType.DAMAGE,
        actor_name="Zhaivra",
        target_name="Goblin",
        action_name="Infused Barb",
        accepted=True,
        hit=True,
        amount=12,
        outcomes=(
            CombatOutcome(CombatOutcomeType.BURN_APPLIED),
            CombatOutcome(CombatOutcomeType.BURN_REFRESHED),
        ),
    )
    ui, _ = _ui(())

    lines = ui._log_lines(entry)

    assert "Goblin began burning." in lines
    assert "Goblin's Burn was refreshed." in lines


def test_poison_outcomes_render_as_secondary_infused_barb_results():
    entry = BattleLogEntry(
        event_type=BattleEventType.DAMAGE,
        actor_name="Zhaivra",
        target_name="Goblin",
        action_name="Infused Barb",
        accepted=True,
        hit=True,
        amount=12,
        outcomes=(
            CombatOutcome(CombatOutcomeType.INFUSED_BARB_CONSUMED),
            CombatOutcome(CombatOutcomeType.POISON_APPLIED),
            CombatOutcome(
                CombatOutcomeType.POISON_TICK,
                amount=5,
                target=CombatOutcomeTarget.ACTOR,
            ),
            CombatOutcome(CombatOutcomeType.POISON_EXPIRED),
        ),
    )
    ui, _ = _ui(())

    assert ui._log_lines(entry) == (
        "Zhaivra used Infused Barb against Goblin. It dealt 12 damage.",
        "Zhaivra loosed the prepared Infused Barb.",
        "Goblin began suffering Poison.",
        "Zhaivra suffered 5 Poison damage.",
        "Goblin's Poison expired.",
    )


def test_infused_barb_primary_resource_consumption_and_burn_render_in_order():
    entry = BattleLogEntry(
        event_type=BattleEventType.DAMAGE,
        actor_name="Zhaivra",
        target_name="Goblin",
        action_name="Infused Barb",
        accepted=True,
        hit=True,
        amount=12,
        resource_spent=5,
        outcomes=(
            CombatOutcome(
                CombatOutcomeType.INFUSED_BARB_CONSUMED,
                target=CombatOutcomeTarget.ACTOR,
            ),
            CombatOutcome(
                CombatOutcomeType.BURN_APPLIED,
                target=CombatOutcomeTarget.TARGET,
            ),
        ),
    )
    ui, _ = _ui(())

    lines = ui._log_lines(entry)

    assert lines == (
        "Zhaivra used Infused Barb against Goblin. It dealt 12 damage.",
        "Resource spent: 5.",
        "Zhaivra loosed the prepared Infused Barb.",
        "Goblin began burning.",
    )


def test_missed_infused_barb_renders_no_duplicate_damage_or_burn_outcome():
    entry = BattleLogEntry(
        event_type=BattleEventType.MISS,
        actor_name="Zhaivra",
        target_name="Goblin",
        action_name="Infused Barb",
        accepted=True,
        hit=False,
        resource_spent=5,
        outcomes=(
            CombatOutcome(
                CombatOutcomeType.INFUSED_BARB_CONSUMED,
                target=CombatOutcomeTarget.ACTOR,
            ),
        ),
    )
    ui, _ = _ui(())

    assert ui._log_lines(entry) == (
        "Zhaivra used Infused Barb against Goblin, but missed.",
        "Resource spent: 5.",
        "Zhaivra loosed the prepared Infused Barb.",
    )


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
        "Ser Branoc used Ironwake Dismemberment against",
    )
    assert _contains(harness, "Critical hit! It")
    assert _contains(harness, "dealt 21 damage.")
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

    assert (
        "Azhvielle used Gravemantle Rupture against Goblin. "
        "It dealt 20 damage."
    ) in text
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
        enemies=(
            EnemyCombatantView(
                "enemy_1",
                "Goblin",
                40,
                60,
                3,
                5,
                20,
                100,
            ),
        ),
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


def test_multi_enemy_layout_preserves_four_authored_labels_at_supported_widths():
    enemies = tuple(
        EnemyCombatantView(
            f"enemy_{index}",
            f"Goblin {index}",
            0 if index == 1 else 60 - index,
            60,
            super_current=0,
            super_maximum=100,
            temporary_labels=("Defeated",) if index == 1 else (),
            defeated=index == 1,
        )
        for index in range(1, 5)
    )
    view = replace(_view(), enemies=enemies)

    for width in (50, 60, 80, 120):
        harness = TerminalHarness()
        ui = TerminalBattleUI(
            input_func=harness.input,
            output_func=harness.output,
            width_provider=lambda width=width: width,
            ansi_enabled=False,
            interactive=False,
        )

        ui.render(view)
        text = "\n".join(harness.lines)

        assert all(len(line) <= width for line in harness.lines)
        for label in ("Goblin 1", "Goblin 2", "Goblin 3", "Goblin 4"):
            assert label in text
        assert "HP 0/60" in text
        assert "Defeated" in text
        assert "VS" in text


def test_four_enemy_turn_log_remains_visible_after_wrapping():
    entries = [
        BattleLogEntry(
            BattleEventType.DAMAGE,
            actor_name="Ser Branoc",
            target_name="Goblin 2",
            action_name="Ironwake Dismemberment",
            accepted=True,
            hit=True,
            amount=21,
        ),
        BattleLogEntry(
            BattleEventType.STATUS,
            actor_name="Ser Branoc",
            target_name="Goblin 2",
            outcomes=(
                CombatOutcome(CombatOutcomeType.BREAK_APPLIED),
                CombatOutcome(CombatOutcomeType.OVERCHARGE_GAINED),
                CombatOutcome(CombatOutcomeType.FROSTBITE_APPLIED),
            ),
        ),
    ]
    for index in range(1, 5):
        entries.append(
            BattleLogEntry(
                BattleEventType.DAMAGE,
                actor_name=f"Goblin {index}",
                target_name="Ser Branoc",
                action_name="Shieldbreaker Chop",
                accepted=True,
                hit=True,
                amount=15,
            )
        )
        entries.append(
            BattleLogEntry(
                BattleEventType.STATUS,
                actor_name=f"Goblin {index}",
                target_name="Ser Branoc",
                outcomes=(
                    CombatOutcome(
                        CombatOutcomeType.BURN_TICK,
                        amount=5,
                        target=CombatOutcomeTarget.ACTOR,
                    ),
                    CombatOutcome(
                        CombatOutcomeType.POISON_TICK,
                        amount=5,
                        target=CombatOutcomeTarget.ACTOR,
                    ),
                    CombatOutcome(
                        CombatOutcomeType.FROSTBITE_TICK,
                        amount=5,
                        target=CombatOutcomeTarget.ACTOR,
                    ),
                ),
            )
        )
    entries.append(
        BattleLogEntry(
            BattleEventType.VICTORY,
            actor_name="Ser Branoc",
            target_name="Goblin 1, Goblin 2, Goblin 3, Goblin 4",
        )
    )
    view = _view(log_entries=tuple(entries))

    for width in (50, 60, 80, 120):
        harness = TerminalHarness()
        ui = TerminalBattleUI(
            input_func=harness.input,
            output_func=harness.output,
            width_provider=lambda width=width: width,
            ansi_enabled=False,
            interactive=False,
        )

        rendered = ui._display_log_lines(view, width)

        assert len(rendered) <= ui.VISIBLE_LOG_LINES
        if width == 50:
            assert len(rendered) == 27
        assert any("Ser Branoc used Ironwake Dismemberment" in line for line in rendered)
        for index in range(1, 5):
            assert any(
                f"Goblin {index} used Shieldbreaker Chop" in line
                for line in rendered
            )
            assert any(
                f"Goblin {index} suffered 5 Burn damage." in line
                for line in rendered
            )
            assert any(
                f"Goblin {index} suffered 5 Poison damage." in line
                for line in rendered
            )
            assert any(
                f"Goblin {index} suffered 5 Frostbite damage." in line
                for line in rendered
            )
        assert any("Ser Branoc is victorious over" in line for line in rendered)


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

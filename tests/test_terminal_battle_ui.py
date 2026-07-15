from app.presentation.battle_models import (
    ActionAvailabilityReason,
    ActionIntent,
    ActionOptionView,
    BattleEventType,
    BattleLogEntry,
    BattleView,
    CombatantView,
    InteractionPhase,
    MoveAvailabilityReason,
    MoveOptionView,
    SuperMeterView,
)
from app.ui.battle_ui import ChooseAction, ChooseMove, GoBack
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
        log_entries=log_entries,
    )


def _ui(inputs):
    harness = TerminalHarness(inputs)
    return TerminalBattleUI(
        input_func=harness.input,
        output_func=harness.output,
        width_provider=lambda: 80,
    ), harness


def test_action_numbers_and_aliases_return_semantic_actions():
    for raw, expected in (("1", ActionIntent.ATTACK), ("defend", ActionIntent.DEFEND)):
        ui, _ = _ui((raw,))
        assert ui.read_input(_view()) == ChooseAction(expected)


def test_super_key_maps_to_semantic_action_from_any_phase():
    ui, _ = _ui(("S",))

    result = ui.read_input(
        _view(phase=InteractionPhase.REGULAR_MOVES, super_ready=True)
    )

    assert result == ChooseAction(ActionIntent.SUPER)


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

    assert "Ser Branoc HP: 116/116" in harness.lines
    assert "Goblin HP: 60/60" in harness.lines
    assert (
        "Ser Branoc used Ironwake Dismemberment. Critical hit! It dealt 21 damage."
        in harness.lines
    )
    assert "Choose an action:" in harness.lines


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
        width_provider=lambda: 45,
    )

    ui.render(
        _view(
            phase=InteractionPhase.REGULAR_MOVES,
            move_options=moves,
        )
    )

    assert "1. Crestgrave Reaping [Normal]" in harness.lines
    assert "2. Cinderlung Vesper [Fire Magic | 3 Mana]" in harness.lines
    assert "3. Brace [Utility | 5 Mana]" in harness.lines
    assert (
        "4. Ironwake Dismemberment [Heavy | Empowered +30%]"
        in harness.lines
    )
    assert not any("[none 0]" in line for line in harness.lines)
    assert all(
        len(line) <= 45
        for line in harness.lines
        if line.startswith("   ")
    )
    assert any(line.startswith("   Brace against") for line in harness.lines)
    assert "0. Back" in harness.lines


def test_back_is_rendered_only_during_move_phases_and_super_is_separate():
    ui, actions = _ui(())
    ui.render(_view())

    assert "0. Back" not in actions.lines
    assert not any(line.startswith("6. Super") for line in actions.lines)

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

    assert "Choose a Super:" in super_menu.lines
    assert "1. Third Gate Obsequy [Super | 100 Super]" in super_menu.lines
    assert "0. Back" in super_menu.lines


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
    ui, harness = _ui(())

    ui.render(_view(log_entries=entries))

    assert "Ser Branoc used Cut. It dealt 7 damage." in harness.lines
    assert "Ser Branoc used Recover. It restored 3 health." in harness.lines
    assert "Goblin used Whiff, but missed." in harness.lines
    assert "Ser Branoc used Blocked, but it failed: rejected." in harness.lines
    assert "Ser Branoc used Brace. It resolved." in harness.lines
    assert "Resource spent: 5." in harness.lines
    assert "Statuses applied: ward." in harness.lines
    assert "Ser Branoc used Defend." in harness.lines


def test_adapter_retains_no_log_or_view_state_and_does_not_mutate_view():
    ui, _ = _ui(())
    view = _view()
    before = repr(view)

    ui.render(view)

    assert repr(view) == before
    assert set(vars(ui)) == {"_input", "_output", "_width_provider"}

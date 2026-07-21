import builtins

import app.game.main_loop as main_loop
from app.enemies.factory import create_enemy_state
from app.game.game_state import GameState
from app.game.main_loop import _startup_game_state
from app.game.overworld_session import OverworldSession, OverworldSessionResult
from app.game.overworld_state import ContextualRoutePhase
from app.game.save_repository import SaveLoadStatus, SaveRepository
from app.player.character import Brawler
from app.player.player_state import PlayerState
from app.presentation.overworld_models import OverworldAction, OverworldScreen
from app.ui.overworld_ui import ChooseOverworldAction
from app.ui.terminal_overworld_ui import TerminalOverworldUI
from app.world.character_profiles.roster import get_profile_by_choice


class ScriptedUI:
    def __init__(self, inputs, before_read=None):
        self.inputs = list(inputs)
        self.views = []
        self.before_read = before_read

    def render(self, view):
        self.views.append(view)

    def read_input(self, view):
        if self.before_read is not None:
            self.before_read(view, self)
        return self.inputs.pop(0)


def _session(game, ui, repository):
    def no_battle(*args, **kwargs):
        raise AssertionError("save/load flow must not create a Battle")

    return OverworldSession(
        game,
        ui=ui,
        battle_factory=no_battle,
        enemy_factory=no_battle,
        battle_ui_factory=no_battle,
        save_repository=repository,
    )


def _saved_game():
    character = get_profile_by_choice("1").create_character()
    player = PlayerState(character, gold=17)
    player.health.take_damage(11)
    player.mana_resource.spend(5)
    player.super_resource.gain(23)
    game = GameState(player)
    game.set_metadata("save-test", "resume")
    game.overworld_state.begin_surface_route()
    game.world_state.mark_encounter_defeated("surface_goblin_solo")
    game.overworld_state.advance_to(
        "surface_goblin_pair",
        contextual_phase=ContextualRoutePhase.ENTER_ENCOUNTER,
    )
    return game


def test_save_from_options_writes_valid_file_and_does_not_change_session(tmp_path):
    game = _saved_game()
    before = game.snapshot()
    repository = SaveRepository(tmp_path / "dungeon_drifters.json")
    ui = ScriptedUI(
        [
            ChooseOverworldAction(OverworldAction.OPTIONS),
            ChooseOverworldAction(OverworldAction.SAVE),
            ChooseOverworldAction(OverworldAction.QUIT),
            ChooseOverworldAction(OverworldAction.CONFIRM),
        ]
    )

    assert _session(game, ui, repository).run() is OverworldSessionResult.QUIT
    assert repository.inspect().status is SaveLoadStatus.VALID
    assert game.snapshot() == before
    assert ui.views[1].screen is OverworldScreen.OPTIONS
    assert ui.views[1].options[0].enabled is True


def test_confirmed_load_replaces_session_and_returns_to_main(tmp_path):
    saved = _saved_game()
    repository = SaveRepository(tmp_path / "dungeon_drifters.json")
    repository.save(saved)
    current = GameState(PlayerState(Brawler()))
    ui = ScriptedUI(
        [
            ChooseOverworldAction(OverworldAction.OPTIONS),
            ChooseOverworldAction(OverworldAction.LOAD),
            ChooseOverworldAction(OverworldAction.CONFIRM),
            ChooseOverworldAction(OverworldAction.OPTIONS),
            ChooseOverworldAction(OverworldAction.QUIT),
            ChooseOverworldAction(OverworldAction.CONFIRM),
        ]
    )
    session = _session(current, ui, repository)

    assert session.run() is OverworldSessionResult.QUIT
    assert session.game_state is not current
    assert session.game_state.overworld_state.current_route_node_id == (
        "surface_goblin_pair"
    )
    assert session.game_state.player_state.gold == 17
    assert [view.screen for view in ui.views[:4]] == [
        OverworldScreen.MAIN,
        OverworldScreen.OPTIONS,
        OverworldScreen.LOAD_CONFIRMATION,
        OverworldScreen.MAIN,
    ]


def test_invalid_load_does_not_mutate_current_session(tmp_path):
    game = GameState(PlayerState(Brawler()))
    repository = SaveRepository(tmp_path / "dungeon_drifters.json")
    repository.save(_saved_game())
    before = game.snapshot()
    corrupted = False

    def corrupt_after_options(view, _ui):
        nonlocal corrupted
        if view.screen is OverworldScreen.OPTIONS and not corrupted:
            repository.path.write_text("not json", encoding="utf-8")
            corrupted = True

    ui = ScriptedUI(
        [
            ChooseOverworldAction(OverworldAction.OPTIONS),
            ChooseOverworldAction(OverworldAction.LOAD),
            ChooseOverworldAction(OverworldAction.CONFIRM),
            ChooseOverworldAction(OverworldAction.QUIT),
            ChooseOverworldAction(OverworldAction.CONFIRM),
        ],
        before_read=corrupt_after_options,
    )

    assert _session(game, ui, repository).run() is OverworldSessionResult.QUIT
    assert game.snapshot() == before
    assert ui.views[3].screen is OverworldScreen.OPTIONS
    assert ui.views[3].notice == (
        "The save file is invalid and was not loaded."
    )


def test_valid_startup_save_loads_without_character_selection(tmp_path, monkeypatch):
    repository = SaveRepository(tmp_path / "dungeon_drifters.json")
    saved = _saved_game()
    repository.save(saved)
    answers = iter(["l"])
    monkeypatch.setattr(builtins, "input", lambda _prompt: next(answers))

    loaded = _startup_game_state(repository)

    assert loaded is not saved
    assert loaded.snapshot() == saved.snapshot()


def test_loaded_session_can_continue_into_the_next_encounter(tmp_path):
    saved = _saved_game()
    repository = SaveRepository(tmp_path / "dungeon_drifters.json")
    repository.save(saved)
    current = GameState(PlayerState(Brawler()))

    class ContinuingBattle:
        def __init__(self, player_state, enemies, *, ui, encounter_label):
            self.player_state = player_state
            self.enemies = tuple(enemies)

        def run(self):
            for enemy in self.enemies:
                enemy.health.take_damage(enemy.health.current)
            return "player"

    ui = ScriptedUI(
        [
            ChooseOverworldAction(OverworldAction.OPTIONS),
            ChooseOverworldAction(OverworldAction.LOAD),
            ChooseOverworldAction(OverworldAction.CONFIRM),
            ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER),
            ChooseOverworldAction(OverworldAction.OPTIONS),
            ChooseOverworldAction(OverworldAction.QUIT),
            ChooseOverworldAction(OverworldAction.CONFIRM),
        ]
    )
    session = OverworldSession(
        current,
        ui=ui,
        battle_factory=ContinuingBattle,
        enemy_factory=create_enemy_state,
        battle_ui_factory=lambda: object(),
        save_repository=repository,
    )

    assert session.run() is OverworldSessionResult.QUIT
    assert session.game_state.overworld_state.current_route_node_id == (
        "surface_warrior_solo"
    )
    assert session.game_state.world_state.defeated_encounters == (
        "surface_goblin_solo",
        "surface_goblin_pair",
    )


def test_main_load_startup_bypasses_new_game_flow(tmp_path, monkeypatch):
    repository = SaveRepository(tmp_path / "dungeon_drifters.json")
    saved = _saved_game()
    repository.save(saved)
    answers = iter(["l"])
    captured = []

    class UnexpectedStory:
        def opening_screen(self):
            raise AssertionError("valid startup load should skip opening flow")

    class UnexpectedEvents:
        def pick_character(self):
            raise AssertionError("valid startup load should skip character selection")

    class CapturingSession:
        def __init__(self, game_state, **_dependencies):
            captured.append(game_state)

        def run(self):
            return OverworldSessionResult.QUIT

    monkeypatch.setattr(builtins, "input", lambda _prompt: next(answers))
    monkeypatch.setattr(main_loop, "StoryElements", UnexpectedStory)
    monkeypatch.setattr(main_loop, "Events", UnexpectedEvents)
    monkeypatch.setattr(main_loop, "OverworldSession", CapturingSession)

    main_loop.main(save_repository=repository)

    assert len(captured) == 1
    assert captured[0] is not saved
    assert captured[0].snapshot() == saved.snapshot()


def test_real_terminal_traverses_options_load_confirmation_without_crashing(
    tmp_path,
):
    repository = SaveRepository(tmp_path / "dungeon_drifters.json")
    repository.save(_saved_game())
    output = []
    inputs = iter(["o", "l", "n", "q", "y"])
    ui = TerminalOverworldUI(
        input_func=lambda _prompt: next(inputs),
        output_func=output.append,
        width_provider=lambda: 80,
        interactive=False,
    )
    current = GameState(PlayerState(Brawler()))

    assert _session(current, ui, repository).run() is OverworldSessionResult.QUIT
    text = "\n".join(output)
    assert "LOAD" in text
    assert "Load the saved session and replace the current session?" in text

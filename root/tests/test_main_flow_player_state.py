import app.game.main_loop as main_loop


class SelectedCharacter:
    name = "Selected Character"


class FakePlayerState:
    instances = []

    def __init__(self, character):
        self.character = character
        self.__class__.instances.append(self)


class FakeGameState:
    instances = []

    def __init__(self, player_state):
        self.player_state = player_state
        self.__class__.instances.append(self)


class FakeEvents:
    selected_character = SelectedCharacter()

    def pick_character(self):
        CALLS.append("pick_character")
        return self.selected_character


class FakeStoryElements:
    def opening_screen(self):
        CALLS.append("opening_screen")


class FakeConsole:
    @staticmethod
    def wait_for_continue():
        CALLS.append("wait_for_continue")

    @staticmethod
    def clear_console():
        CALLS.append("clear_console")


class FakeOverworldUI:
    instances = []

    def __init__(self):
        self.__class__.instances.append(self)


class FakeBattleUI:
    instances = []

    def __init__(self):
        self.__class__.instances.append(self)


class FakeOverworldSession:
    instances = []

    def __init__(self, game_state, **dependencies):
        self.game_state = game_state
        self.dependencies = dependencies
        self.run_called = False
        self.__class__.instances.append(self)

    def run(self):
        self.run_called = True
        return "quit"


CALLS = []


def test_main_builds_one_persistent_session_from_the_selected_character():
    originals = {
        "PlayerState": main_loop.PlayerState,
        "GameState": main_loop.GameState,
        "Events": main_loop.Events,
        "StoryElements": main_loop.StoryElements,
        "OverworldSession": main_loop.OverworldSession,
        "TerminalOverworldUI": main_loop.TerminalOverworldUI,
        "TerminalBattleUI": main_loop.TerminalBattleUI,
        "console": main_loop.console,
    }
    CALLS.clear()
    FakePlayerState.instances = []
    FakeGameState.instances = []
    FakeOverworldUI.instances = []
    FakeBattleUI.instances = []
    FakeOverworldSession.instances = []
    selected_character = FakeEvents.selected_character

    main_loop.PlayerState = FakePlayerState
    main_loop.GameState = FakeGameState
    main_loop.Events = FakeEvents
    main_loop.StoryElements = FakeStoryElements
    main_loop.OverworldSession = FakeOverworldSession
    main_loop.TerminalOverworldUI = FakeOverworldUI
    main_loop.TerminalBattleUI = FakeBattleUI
    main_loop.console = FakeConsole

    try:
        main_loop.main()
    finally:
        for name, value in originals.items():
            setattr(main_loop, name, value)

    assert len(FakePlayerState.instances) == 1
    player_state = FakePlayerState.instances[0]
    assert player_state.character is selected_character
    assert len(FakeGameState.instances) == 1
    game_state = FakeGameState.instances[0]
    assert game_state.player_state is player_state
    assert len(FakeOverworldSession.instances) == 1
    session = FakeOverworldSession.instances[0]
    assert session.game_state is game_state
    assert session.run_called is True
    assert isinstance(session.dependencies["ui"], FakeOverworldUI)
    assert session.dependencies["battle_factory"] is main_loop.Battle
    assert session.dependencies["enemy_factory"] is main_loop.create_enemy_state
    assert session.dependencies["battle_ui_factory"] is FakeBattleUI
    assert CALLS == [
        "opening_screen",
        "wait_for_continue",
        "clear_console",
        "pick_character",
        "clear_console",
    ]

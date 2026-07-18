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
    instances = []
    calls = []

    def __init__(self):
        self.__class__.instances.append(self)

    def pick_character(self):
        CALLS.append("pick_character")
        self.__class__.calls.append("pick_character")
        return self.selected_character


class FakeStoryElements:
    encounter = "battle"
    instances = []

    def __init__(self):
        self.opening_screen_called = False
        self.day_one_events = None
        self.escaped_character = None
        self.battle_ending_character = None
        self.battle_ending_winner = None
        self.__class__.instances.append(self)

    def opening_screen(self):
        CALLS.append("opening_screen")
        self.opening_screen_called = True

    def day_one(self, events):
        CALLS.append("day_one")
        self.day_one_events = events
        return self.encounter

    def escaped_ending(self, character):
        self.escaped_character = character

    def battle_ending(self, character, winner):
        self.battle_ending_character = character
        self.battle_ending_winner = winner


class FakeEnemyFactory:
    calls = []
    enemy_state = object()

    @classmethod
    def create_enemy_state(cls, enemy_type, tier=0):
        cls.calls.append((enemy_type, tier))
        return cls.enemy_state


class FakeBattle:
    instances = []

    def __init__(self, player_state, foe, *, ui):
        self.player_state = player_state
        self.foe = foe
        self.ui = ui
        self.__class__.instances.append(self)

    def run(self):
        return "player"


class FakeConsole:
    @staticmethod
    def wait_for_continue():
        CALLS.append("wait_for_continue")

    @staticmethod
    def clear_console():
        CALLS.append("clear_console")


class FakeTerminalBattleUI:
    instances = []

    def __init__(self):
        self.__class__.instances.append(self)


CALLS = []


def reset_fakes():
    CALLS.clear()
    FakePlayerState.instances = []
    FakeGameState.instances = []
    FakeEvents.instances = []
    FakeEvents.selected_character = SelectedCharacter()
    FakeEvents.calls = []
    FakeStoryElements.instances = []
    FakeStoryElements.encounter = "battle"
    FakeEnemyFactory.calls = []
    FakeEnemyFactory.enemy_state = object()
    FakeBattle.instances = []
    FakeTerminalBattleUI.instances = []


def run_with_fakes(encounter):
    reset_fakes()
    FakeStoryElements.encounter = encounter

    original_player_state = main_loop.PlayerState
    original_game_state = main_loop.GameState
    original_events = main_loop.Events
    original_story_elements = main_loop.StoryElements
    original_battle = main_loop.Battle
    original_create_enemy_state = main_loop.create_enemy_state
    original_console = main_loop.console
    original_terminal_battle_ui = main_loop.TerminalBattleUI

    main_loop.PlayerState = FakePlayerState
    main_loop.GameState = FakeGameState
    main_loop.Events = FakeEvents
    main_loop.StoryElements = FakeStoryElements
    main_loop.Battle = FakeBattle
    main_loop.create_enemy_state = FakeEnemyFactory.create_enemy_state
    main_loop.console = FakeConsole
    main_loop.TerminalBattleUI = FakeTerminalBattleUI

    try:
        main_loop.main()
    finally:
        main_loop.PlayerState = original_player_state
        main_loop.GameState = original_game_state
        main_loop.Events = original_events
        main_loop.StoryElements = original_story_elements
        main_loop.Battle = original_battle
        main_loop.create_enemy_state = original_create_enemy_state
        main_loop.console = original_console
        main_loop.TerminalBattleUI = original_terminal_battle_ui

    return FakeEvents.selected_character, FakeStoryElements.instances[0], list(CALLS)


def test_escape_path_wraps_character_once_and_skips_battle():
    selected_character, story, calls = run_with_fakes("escaped")

    assert len(FakePlayerState.instances) == 1
    player_state = FakePlayerState.instances[0]
    assert player_state.character is selected_character
    assert len(FakeGameState.instances) == 1
    assert FakeGameState.instances[0].player_state is player_state
    assert story.escaped_character is selected_character
    assert story.battle_ending_character is None
    assert FakeBattle.instances == []
    assert FakeEnemyFactory.calls == []
    assert calls == ["opening_screen", "wait_for_continue", "clear_console", "pick_character", "clear_console", "day_one"]


def test_battle_path_wraps_character_once_and_uses_wrapped_character():
    selected_character, story, calls = run_with_fakes("battle")
    player_state = FakePlayerState.instances[0]

    assert len(FakePlayerState.instances) == 1
    assert player_state.character is selected_character
    assert len(FakeGameState.instances) == 1
    assert FakeGameState.instances[0].player_state is player_state
    assert len(FakeBattle.instances) == 1
    assert FakeBattle.instances[0].player_state is FakeGameState.instances[0].player_state
    assert FakeEnemyFactory.calls == [("goblin", 0)]
    assert FakeBattle.instances[0].foe is FakeEnemyFactory.enemy_state
    assert len(FakeTerminalBattleUI.instances) == 1
    assert FakeBattle.instances[0].ui is FakeTerminalBattleUI.instances[0]
    assert story.escaped_character is None
    assert story.battle_ending_character is selected_character
    assert story.battle_ending_winner == "player"
    assert calls == ["opening_screen", "wait_for_continue", "clear_console", "pick_character", "clear_console", "day_one"]

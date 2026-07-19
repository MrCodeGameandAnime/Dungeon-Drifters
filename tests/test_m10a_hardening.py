import pytest

from app.game.game_state import GameState
from app.game.overworld_session import OverworldSession, OverworldSessionResult
from app.player.player_state import PlayerState
from app.presentation.overworld_presenter import OverworldPresenter
from app.ui.terminal_overworld_ui import TerminalOverworldUI
from app.world.character_profiles.roster import get_character_profiles


class EnemyFactory:
    def __init__(self):
        self.enemies = []

    def __call__(self, archetype_id, *, tier):
        enemy = object()
        self.enemies.append(enemy)
        return enemy


def terminal_ui(inputs, output):
    values = iter(inputs)
    return TerminalOverworldUI(
        input_func=lambda prompt: next(values),
        output_func=output.append,
        width_provider=lambda: 100,
        unicode_enabled=False,
        ansi_enabled=True,
        interactive=True,
    )


@pytest.mark.parametrize("profile", get_character_profiles())
def test_every_drifter_can_navigate_the_complete_terminal_menu_shell(profile):
    player = PlayerState(profile.create_character())
    game = GameState(player)
    before = game.snapshot()
    output = []
    inputs = (
        "c",
        "s", "b",
        "w", "b",
        "e", "b",
        "b",
        "i", "b",
        "m", "b",
        "o", "q", "n", "b",
        "o", "q", "y",
    )
    session = OverworldSession(
        game,
        ui=terminal_ui(inputs, output),
        presenter=OverworldPresenter(),
        battle_factory=lambda *args, **kwargs: None,
        enemy_factory=lambda *args, **kwargs: None,
        battle_ui_factory=lambda: None,
    )

    result = session.run()
    text = "\n".join(output)

    assert result is OverworldSessionResult.QUIT
    assert profile.display_name in text
    assert player.get_equipped("weapon").name in text
    assert player.combat_moves[0].name in text
    for heading in (
        "OVERWORLD",
        "CHARACTER",
        "SKILLS",
        "WEAPON",
        "EQUIPMENT",
        "ITEMS",
        "MAP",
        "OPTIONS",
        "QUIT",
    ):
        assert heading in text
    assert "surface_goblin" not in text
    assert "ember_shard" not in text
    assert "deep_coal" not in text
    assert "night_berry" not in text
    assert game.snapshot() == before


def test_post_battle_overworld_render_clears_the_final_battle_frame():
    profile = get_character_profiles()[0]
    player = PlayerState(profile.create_character())
    game = GameState(player)
    output = []
    enemy_factory = EnemyFactory()

    class WinningBattle:
        def __init__(self, acting_player, enemy, *, ui):
            assert acting_player is player
            self.enemy = enemy

        def run(self):
            output.append("FINAL BATTLE FRAME")
            player.health.take_damage(7)
            return "player"

    session = OverworldSession(
        game,
        ui=terminal_ui(("e", "o", "q", "y"), output),
        battle_factory=WinningBattle,
        enemy_factory=enemy_factory,
        battle_ui_factory=lambda: object(),
    )

    session.run()

    marker_index = output.index("FINAL BATTLE FRAME")
    first_overworld_line = output[marker_index + 1]
    assert first_overworld_line.startswith("\033[2J\033[H+")
    assert "OVERWORLD  |  Goblin Pair" in output[marker_index + 2]
    assert player.health.current == player.health.maximum - 7
    assert len(enemy_factory.enemies) == 1


def test_transient_screen_selection_notice_and_confirmation_never_enter_snapshot():
    profile = get_character_profiles()[2]
    game = GameState(PlayerState(profile.create_character()))
    baseline = game.snapshot()
    output = []
    inputs = ("i", "1", "i", "b", "b", "o", "q", "n", "b", "o", "q", "y")
    session = OverworldSession(
        game,
        ui=terminal_ui(inputs, output),
        battle_factory=lambda *args, **kwargs: None,
        enemy_factory=lambda *args, **kwargs: None,
        battle_ui_factory=lambda: None,
    )

    session.run()

    assert game.snapshot() == baseline
    snapshot_text = repr(game.snapshot()).lower()
    assert "screen" not in snapshot_text
    assert "selection" not in snapshot_text
    assert "confirmation" not in snapshot_text

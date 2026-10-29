from app.combat.battle import Battle
from app.content.catalog import create_enemy_state, get_drifter_spec
from app.player.player_state import PlayerState
from app.presentation.overworld_models import (
    OutingRewardsView,
    OverworldAction,
    OverworldOptionView,
    OverworldScreen,
    OverworldView,
)
from app.ui.overworld_ui import ChooseOverworldAction
from app.ui.terminal_battle_ui import TerminalBattleUI
from app.ui.terminal_overworld_ui import TerminalOverworldUI


class StableRng:
    def randint(self, _minimum, _maximum):
        return 1

    def choice(self, values):
        return values[0]


def test_terminal_battle_shows_both_drifters_and_marks_the_active_actor():
    lead = PlayerState(get_drifter_spec("branoc").create_character())
    companion = PlayerState(get_drifter_spec("azhvielle").create_character())
    battle = Battle(
        lead,
        (create_enemy_state("goblin"),),
        party=(companion,),
        rng=StableRng(),
    )
    output = []
    ui = TerminalBattleUI(
        output_func=output.append,
        width_provider=lambda: 100,
        interactive=False,
    )

    ui.render(battle.current_view())

    rendered = "\n".join(output)
    assert "Ser Branoc" in rendered
    assert "Azhvielle" in rendered
    assert "ACTIVE" in rendered
    assert "Goblin" in rendered


def test_terminal_extraction_shows_pending_rewards_and_returns_semantic_action():
    view = OverworldView(
        screen=OverworldScreen.EXTRACTION,
        location_label="Floor 1 Hub",
        adventure_text="The Goblin trio is defeated.",
        options=(
            OverworldOptionView(
                OverworldAction.RETURN_TO_HUB,
                "Return to Hub",
                True,
            ),
        ),
        outing_rewards=OutingRewardsView(experience=120, gold=9),
    )
    output = []
    ui = TerminalOverworldUI(
        input_func=lambda _prompt: "h",
        output_func=output.append,
        width_provider=lambda: 100,
        interactive=False,
    )

    ui.render(view)
    selected = ui.read_input(view)

    rendered = "\n".join(output)
    assert "120" in rendered and "EXP" in rendered
    assert "9" in rendered and "gold" in rendered
    assert selected == ChooseOverworldAction(OverworldAction.RETURN_TO_HUB)

import pytest

from app.game.game_state import GameState
from app.game.overworld_session import OverworldSession, OverworldSessionResult
from app.game.overworld_state import ContextualRoutePhase
from app.player.character import Brawler, BlackMage
from app.player.progression import MAXIMUM_LEVEL, xp_required_for_next_level
from app.player.player_state import PlayerState
from app.presentation.overworld_models import OverworldAction
from app.ui.overworld_ui import ChooseOverworldAction


class GrowthSessionUI:
    def __init__(self):
        self.inputs = iter(
            (
                ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER),
                ChooseOverworldAction(OverworldAction.OPTIONS),
                ChooseOverworldAction(OverworldAction.QUIT),
                ChooseOverworldAction(OverworldAction.CONFIRM),
            )
        )

    def render(self, _view):
        return None

    def read_input(self, _view):
        return next(self.inputs)


class GrowthStubEnemy:
    def __init__(self):
        self.alive = True

    def is_alive(self):
        return self.alive


class GrowthEnemyFactory:
    def __call__(self, _archetype_id, *, tier):
        assert tier == 0
        return GrowthStubEnemy()


class GrowthBattleFactory:
    def __call__(self, player_state, enemies, *, ui, encounter_label=None):
        class WinningBattle:
            def __init__(self):
                self.player_state = player_state
                self.enemies = tuple(enemies)
                self.ui = ui
                self.encounter_label = encounter_label

            def run(self):
                for enemy in self.enemies:
                    enemy.alive = False
                return "player"

        return WinningBattle()


def run_rewarded_encounter(game):
    result = OverworldSession(
        game,
        ui=GrowthSessionUI(),
        battle_factory=GrowthBattleFactory(),
        enemy_factory=GrowthEnemyFactory(),
        battle_ui_factory=lambda: None,
    ).run()
    assert result is OverworldSessionResult.QUIT


def test_player_growth_starts_at_zero_and_level_gain_grants_points_and_resources():
    player = PlayerState(BlackMage())
    player.health.take_damage(7)
    player.mana_resource.spend(8)

    assert player.gain_experience(100) == 1
    assert player.level_state.current == 2
    assert player.exp_state.current == 0
    assert player.growth_points == 3
    assert player.health.maximum == 95
    assert player.health.current == 88
    assert player.mana_resource.maximum == 57
    assert player.mana_resource.current == 49


def test_multiple_level_gain_grants_three_points_per_level():
    player = PlayerState(Brawler())

    assert player.gain_experience(350) == 3
    assert player.level_state.current == 4
    assert player.exp_state.current == 31
    assert player.growth_points == 9
    assert player.health.maximum == 128
    assert player.mana_resource.maximum == 49


@pytest.mark.parametrize(
    "stat_name",
    ("constitution", "spirit", "intelligence", "strength", "dexterity", "intuition"),
)
def test_one_growth_point_increases_each_permanent_stat(stat_name):
    player = PlayerState(Brawler())
    player.gain_experience(100)
    before = player.character.permanent_stats.get_stat(stat_name)

    assert player.increase_permanent_stat(stat_name) == before + 1
    assert player.character.permanent_stats.get_stat(stat_name) == before + 1
    assert player.growth_points == 2


def test_constitution_and_spirit_growth_updates_resources_without_full_refill():
    player = PlayerState(Brawler())
    player.gain_experience(100)
    player.health.take_damage(10)
    player.mana_resource.spend(5)

    health_before = (player.health.current, player.health.maximum)
    mana_before = (player.mana_resource.current, player.mana_resource.maximum)

    player.increase_permanent_stat("constitution")
    assert player.health.maximum == health_before[1] + 4
    assert player.health.current == health_before[0] + 4

    player.increase_permanent_stat("spirit")
    assert player.mana_resource.maximum == mana_before[1] + 1
    assert player.mana_resource.current == mana_before[0] + 1


def test_non_resource_stat_growth_does_not_change_hp_or_mana():
    player = PlayerState(Brawler())
    player.gain_experience(100)
    before = (
        player.health.current,
        player.health.maximum,
        player.mana_resource.current,
        player.mana_resource.maximum,
    )

    player.increase_permanent_stat("strength")

    assert (
        player.health.current,
        player.health.maximum,
        player.mana_resource.current,
        player.mana_resource.maximum,
    ) == before


def test_growth_uses_permanent_stat_not_equipped_weapon_bonus():
    player = PlayerState(Brawler())
    player.gain_experience(100)

    assert player.effective_stat("strength") == 18
    assert player.increase_permanent_stat("strength") == 16
    assert player.character.permanent_stats.strength == 16
    assert player.effective_stat("strength") == 19


@pytest.mark.parametrize("stat_name", ("invalid", "", None))
def test_invalid_growth_name_changes_nothing(stat_name):
    player = PlayerState(Brawler())
    before = player.snapshot()

    with pytest.raises((TypeError, ValueError)):
        player.increase_permanent_stat(stat_name)

    assert player.snapshot() == before


def test_growth_without_points_and_at_stat_cap_changes_nothing():
    player = PlayerState(Brawler())
    before = player.snapshot()

    with pytest.raises(ValueError, match="no Growth Points"):
        player.increase_permanent_stat("strength")
    assert player.snapshot() == before

    player.gain_experience(100)
    player.character.strength = 100
    before = player.snapshot()
    with pytest.raises(ValueError, match="maximum"):
        player.increase_permanent_stat("strength")
    assert player.snapshot() == before


def test_growth_points_are_present_in_defensive_snapshot():
    player = PlayerState(Brawler())
    player.gain_experience(100)
    player.increase_permanent_stat("constitution")

    snapshot = player.snapshot()
    snapshot["progression"]["growth_points"] = 999

    assert player.growth_points == 2
    assert player.snapshot()["progression"]["growth_points"] == 2


@pytest.mark.parametrize(
    "exp_reward, gold_reward",
    ((-1, 4), (True, 4), (40, -1), (40, True)),
)
def test_encounter_reward_validates_all_values_before_mutation(
    exp_reward,
    gold_reward,
):
    player = PlayerState(Brawler(), gold=7)
    before = player.snapshot()

    with pytest.raises((TypeError, ValueError)):
        player.apply_encounter_reward(exp_reward, gold_reward)

    assert player.snapshot() == before


def test_encounter_reward_applies_gold_and_growth_atomically():
    player = PlayerState(Brawler(), gold=7)
    player.health.take_damage(10)
    player.mana_resource.spend(5)

    assert player.apply_encounter_reward(100, 6) == 1
    assert player.gold == 13
    assert player.level_state.current == 2
    assert player.exp_state.current == 0
    assert player.growth_points == 3
    assert player.health.maximum == 120
    assert player.health.current == 110
    assert player.mana_resource.maximum == 47
    assert player.mana_resource.current == 42


def test_surface_route_rewards_match_the_locked_cumulative_progression():
    player = PlayerState(Brawler())
    game = GameState(player)
    expected = (
        ("surface_goblin_solo", 1, 40, 116, 46, 0, 3),
        ("surface_goblin_pair", 2, 20, 120, 47, 3, 9),
        ("surface_warrior_solo", 2, 80, 120, 47, 3, 14),
        ("surface_warrior_pair", 3, 94, 124, 48, 6, 24),
        ("surface_shaman_solo", 4, 71, 128, 49, 9, 31),
        ("surface_shaman_pair", 6, 4, 136, 51, 15, 45),
        ("surface_elite_patrol", 7, 60, 140, 52, 18, 57),
        ("surface_goblin_lord", 9, 68, 148, 54, 24, 75),
    )

    for index, (encounter_id, level, exp, hp, mana, points, gold) in enumerate(
        expected
    ):
        if game.overworld_state.current_route_node_id != encounter_id:
            game.overworld_state.advance_to(
                encounter_id,
                contextual_phase=ContextualRoutePhase.ENTER_ENCOUNTER,
            )

        run_rewarded_encounter(game)

        assert player.level_state.current == level
        assert player.exp_state.current == exp
        assert player.health.maximum == hp
        assert player.mana_resource.maximum == mana
        assert player.growth_points == points
        assert player.gold == gold
        assert game.world_state.defeated_encounters == tuple(
            entry[0] for entry in expected[: index + 1]
        )

    assert player.health.maximum == 116 + 32
    assert player.mana_resource.maximum == 46 + 8


def test_player_growth_reaches_cap_and_discards_excess_without_more_points():
    player = PlayerState(Brawler())
    player.level_state.current = MAXIMUM_LEVEL - 1
    amount = xp_required_for_next_level(MAXIMUM_LEVEL - 1) + 999

    assert player.gain_experience(amount) == 1
    assert player.level_state.current == MAXIMUM_LEVEL
    assert player.exp_state.current == 0
    assert player.growth_points == 3

    assert player.gain_experience(999999) == 0
    assert player.exp_state.current == 0
    assert player.growth_points == 3

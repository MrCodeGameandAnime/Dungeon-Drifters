import pytest

from app.game.party_state import DungeonPhase
from app.persistence.save_document import build_save_document, reconstruct_game_state
from tests.game_test_support import (
    completed_hub_game,
    floor_one_rest_game,
    hub_game,
    recruited_pair_game,
)


@pytest.mark.parametrize(
    "builder,phase,companions",
    (
        (hub_game, DungeonPhase.HUB, 0),
        (recruited_pair_game, DungeonPhase.PARTY_READY, 1),
        (completed_hub_game, DungeonPhase.HUB, 1),
        (floor_one_rest_game, DungeonPhase.OUTING, 1),
    ),
)
def test_scenario_builders_create_valid_independent_persistable_states(builder, phase, companions):
    game = builder()
    other = builder()
    assert game.party_state.phase is phase
    assert len(game.party_state.companions) == companions
    assert reconstruct_game_state(build_save_document(game)).snapshot() == game.snapshot()
    before = other.snapshot()
    game.party_state.add_shared_items({"grade_i_metal": 2})
    game.player_state.health.take_damage(1)
    assert other.snapshot() == before

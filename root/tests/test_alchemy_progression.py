import copy

import pytest

from app.game.alchemy import AlchemyService, AlchemyStatus
from app.persistence.ports import SaveLoadResult
from app.persistence.save_port_contract import SaveLoadStatus
from tests.game_test_support import hub_game


class MemorySavePort:
    def __init__(self, status=SaveLoadStatus.SAVED):
        self.status = status
        self.saved_states = []

    def inspect(self):
        return SaveLoadResult(SaveLoadStatus.MISSING)

    def load(self):
        return SaveLoadResult(SaveLoadStatus.MISSING)

    def save(self, game_state):
        if self.status is SaveLoadStatus.SAVED:
            self.saved_states.append(game_state.clone())
        return SaveLoadResult(self.status)


def test_alchemy_craft_uses_current_mastery_output_and_awards_recipe_xp_once():
    game = hub_game(gold=100)
    game.party_state.add_shared_items({"medicinal_herb": 2, "clean_water": 2})
    game.party_state.hub_economy_state.add_alchemy_experience(1200)
    service = AlchemyService(save_port=MemorySavePort())

    result = service.craft(
        game,
        recipe_id="healing_potion",
        expected_transaction_sequence=0,
    )

    assert result.status is AlchemyStatus.CRAFTED
    assert result.game_state.party_state.shared_items == {
        "healing_potion": 2,
        "medicinal_herb": 1,
        "clean_water": 1,
    }
    assert result.game_state.party_state.hub_economy_state.alchemy_experience == 1210
    assert result.game_state.party_state.hub_economy_state.alchemy_level == 25
    assert result.game_state.party_state.crafting_experience == 0


def test_alchemy_craft_rejects_stale_repeat_without_second_output_or_xp():
    game = hub_game()
    game.party_state.add_shared_items({"charcoal_dust": 2, "sulfur": 2})
    service = AlchemyService(save_port=MemorySavePort())

    first = service.craft(
        game,
        recipe_id="smoke_bomb",
        expected_transaction_sequence=0,
    )
    repeated = service.craft(
        first.game_state,
        recipe_id="smoke_bomb",
        expected_transaction_sequence=0,
    )

    assert first.status is AlchemyStatus.CRAFTED
    assert repeated.status is AlchemyStatus.STALE_TRANSACTION
    assert first.game_state.party_state.shared_items["smoke_bomb"] == 1
    assert first.game_state.party_state.shared_items["charcoal_dust"] == 1
    assert first.game_state.party_state.shared_items["sulfur"] == 1
    assert first.game_state.party_state.hub_economy_state.alchemy_experience == 15


def test_alchemy_craft_save_failure_leaves_resources_output_xp_and_sequence_unchanged():
    game = hub_game()
    game.party_state.add_shared_items({"magic_reagent": 1, "aether_dust": 1})
    before = copy.deepcopy(game.snapshot())
    service = AlchemyService(save_port=MemorySavePort(SaveLoadStatus.INVALID))

    result = service.craft(
        game,
        recipe_id="mana_potion",
        expected_transaction_sequence=0,
    )

    assert result.status is AlchemyStatus.SAVE_FAILED
    assert result.game_state is game
    assert game.snapshot() == before


def test_rare_return_talisman_requires_confirmation_and_commits_exact_recipe():
    game = hub_game()
    game.party_state.add_shared_items({"goblin_lord_core": 2, "mythril_plate": 1})
    service = AlchemyService(save_port=MemorySavePort())
    preview = service.preview_return_talisman(
        game,
        expected_transaction_sequence=0,
    )
    before_xp = game.party_state.hub_economy_state.alchemy_experience

    required = service.craft_return_talisman(
        game,
        expected_transaction_sequence=0,
    )
    cancelled = service.cancel_return_talisman(game, preview)
    crafted = service.craft_return_talisman(
        game,
        expected_transaction_sequence=0,
        confirmation=preview,
    )

    assert required.status is AlchemyStatus.CONFIRMATION_REQUIRED
    assert cancelled.status is AlchemyStatus.CANCELLED
    assert crafted.status is AlchemyStatus.CRAFTED
    assert crafted.game_state.party_state.shared_items == {"return_talisman": 1}
    assert crafted.game_state.party_state.hub_economy_state.alchemy_experience == before_xp
    assert crafted.game_state.party_state.crafting_experience == 0


def test_rare_return_talisman_save_failure_preserves_inputs_and_output():
    game = hub_game()
    game.party_state.add_shared_items({"goblin_lord_core": 2, "mythril_plate": 1})
    before = copy.deepcopy(game.snapshot())
    service = AlchemyService(save_port=MemorySavePort(SaveLoadStatus.INVALID))
    preview = service.preview_return_talisman(
        game,
        expected_transaction_sequence=0,
    )

    result = service.craft_return_talisman(
        game,
        expected_transaction_sequence=0,
        confirmation=preview,
    )

    assert result.status is AlchemyStatus.SAVE_FAILED
    assert result.game_state is game
    assert game.snapshot() == before


@pytest.mark.parametrize(
    ("experience", "level"),
    ((0, 1), (1200, 25), (2450, 50), (3700, 75), (4950, 100), (7000, 100)),
)
def test_alchemy_level_uses_approved_thresholds_and_cap(experience, level):
    game = hub_game()
    economy = game.party_state.hub_economy_state

    economy.add_alchemy_experience(experience)

    assert economy.alchemy_level == level
    assert economy.alchemy_experience == experience

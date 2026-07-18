import pytest

from app.combat.battle import Battle
from app.enemies.goblin.definition import Goblin
from app.enemies.state import EnemyState
from app.player.character import BlackMage, Brawler, Monk, RogueArcher
from app.player.character_run_state import (
    FIRE_INFUSION_REQUIREMENTS,
    CharacterRunState,
    InfusionKind,
    PreparedPayloadId,
    RunItemId,
)
from app.player.player_state import PlayerState


class UnusedUI:
    def render(self, view):
        raise AssertionError("battle rendering is not expected")

    def read_input(self, view):
        raise AssertionError("battle input is not expected")


def test_zhaivra_starts_with_personal_compounds_and_unprepared_payload():
    player = PlayerState(RogueArcher())
    run_state = player.character_run_state

    assert run_state.item_quantity(RunItemId.EMBER_SHARD) == 1
    assert run_state.item_quantity(RunItemId.DEEP_COAL) == 1
    assert run_state.item_quantity(RunItemId.NIGHT_BERRY) == 1
    assert run_state.supports_payload(PreparedPayloadId.INFUSED_BARB) is True
    assert run_state.payload_prepared(PreparedPayloadId.INFUSED_BARB) is False


@pytest.mark.parametrize("character_type", (Brawler, BlackMage, Monk))
def test_other_drifters_do_not_receive_zhaivra_run_resources(character_type):
    run_state = PlayerState(character_type()).character_run_state

    assert run_state.item_quantity(RunItemId.EMBER_SHARD) == 0
    assert run_state.item_quantity(RunItemId.DEEP_COAL) == 0
    assert run_state.supports_payload(PreparedPayloadId.INFUSED_BARB) is False
    assert run_state.snapshot() == {"inventory": {}, "prepared_payloads": {}}


def test_character_run_state_is_not_shared_between_players():
    first = PlayerState(RogueArcher())
    second = PlayerState(RogueArcher())

    assert first.character_run_state is not second.character_run_state
    assert first.character_run_state.snapshot() == second.character_run_state.snapshot()


def test_character_run_state_persists_when_player_enters_new_encounters():
    player = PlayerState(RogueArcher())
    run_state = player.character_run_state

    first = Battle(player, EnemyState(Goblin()), ui=UnusedUI())
    second = Battle(player, EnemyState(Goblin()), ui=UnusedUI())

    assert first.player_state.character_run_state is run_state
    assert second.player_state.character_run_state is run_state


def test_run_state_snapshot_is_deterministic_and_separate_from_equipment_inventory():
    player = PlayerState(RogueArcher())

    assert player.inventory.items == ()
    assert player.character_run_state.snapshot() == {
        "inventory": {
            "deep_coal": 1,
            "ember_shard": 1,
            "night_berry": 1,
        },
        "prepared_payloads": {
            "infused_barb": None,
        },
    }
    assert player.snapshot()["run_state"] == player.character_run_state.snapshot()


def test_character_run_state_rejects_invalid_authored_values():
    with pytest.raises(ValueError):
        CharacterRunState(inventory={"unknown": 1})
    with pytest.raises(ValueError):
        CharacterRunState(inventory={RunItemId.EMBER_SHARD: -1})
    with pytest.raises(TypeError):
        CharacterRunState(inventory={RunItemId.EMBER_SHARD: True})
    with pytest.raises(ValueError):
        CharacterRunState(
            prepared_payloads={PreparedPayloadId.INFUSED_BARB: 1}
        )


def test_prepared_payload_consumption_is_atomic_and_requires_active_state():
    run_state = PlayerState(RogueArcher()).character_run_state
    run_state.prepare_payload(
        PreparedPayloadId.INFUSED_BARB,
        FIRE_INFUSION_REQUIREMENTS,
    )

    run_state.consume_payload(PreparedPayloadId.INFUSED_BARB)

    assert run_state.payload_prepared(PreparedPayloadId.INFUSED_BARB) is False
    assert run_state.prepared_infusion() is None
    with pytest.raises(ValueError):
        run_state.consume_payload(PreparedPayloadId.INFUSED_BARB)
    with pytest.raises(ValueError):
        PlayerState(Brawler()).character_run_state.consume_payload(
            PreparedPayloadId.INFUSED_BARB
        )


def test_prepared_infused_barb_payload_is_typed_and_snapshotted():
    run_state = CharacterRunState(
        prepared_payloads={
            PreparedPayloadId.INFUSED_BARB: InfusionKind.POISON,
        }
    )

    assert run_state.prepared_infusion() is InfusionKind.POISON
    assert run_state.snapshot()["prepared_payloads"] == {"infused_barb": "poison"}
    assert run_state.consume_infusion() is InfusionKind.POISON
    assert run_state.snapshot()["prepared_payloads"] == {"infused_barb": None}

import pytest

from app.player.character import RogueArcher
from app.player.character_run_state import (
    FIRE_INFUSION_REQUIREMENTS,
    InfusionKind,
    PreparedPayloadId,
    RunItemId,
)
from app.player.player_state import PlayerBattleCheckpoint, PlayerState


def test_checkpoint_is_immutable_and_rejects_wrong_restore_type():
    player = PlayerState(RogueArcher())
    checkpoint = player.create_battle_checkpoint()

    with pytest.raises(AttributeError):
        checkpoint.health_current = 1
    with pytest.raises(TypeError, match="PlayerBattleCheckpoint"):
        player.restore_battle_checkpoint(object())
    assert isinstance(checkpoint, PlayerBattleCheckpoint)


def test_checkpoint_restores_all_battle_mutable_persistent_values():
    player = PlayerState(RogueArcher())
    checkpoint = player.create_battle_checkpoint()

    player.health.take_damage(19)
    assert player.mana_resource.spend(7) is True
    player.super_resource.gain(45)
    player.character_run_state.prepare_infusion(
        InfusionKind.FIRE,
        FIRE_INFUSION_REQUIREMENTS,
    )

    player.restore_battle_checkpoint(checkpoint)

    assert player.health.current == player.health.maximum
    assert player.mana_resource.current == player.mana_resource.maximum
    assert player.super_resource.current == 0
    assert player.character_run_state.item_quantity(RunItemId.EMBER_SHARD) == 1
    assert player.character_run_state.item_quantity(RunItemId.DEEP_COAL) == 1
    assert player.character_run_state.item_quantity(RunItemId.NIGHT_BERRY) == 1
    assert player.character_run_state.payload_prepared(
        PreparedPayloadId.INFUSED_BARB
    ) is False


def test_checkpoint_restore_preserves_the_complete_live_owner_graph():
    player = PlayerState(RogueArcher())
    character = player.character
    health = player.health
    mana = player.mana_resource
    super_resource = player.super_resource
    inventory = player.inventory
    run_state = player.character_run_state
    weapon = player.get_equipped("weapon")
    checkpoint = player.create_battle_checkpoint()

    player.health.take_damage(5)
    player.mana_resource.spend(5)
    player.super_resource.gain(10)
    player.restore_battle_checkpoint(checkpoint)

    assert player.character is character
    assert player.health is health
    assert player.mana_resource is mana
    assert player.super_resource is super_resource
    assert player.inventory is inventory
    assert player.character_run_state is run_state
    assert player.get_equipped("weapon") is weapon


def test_checkpoint_and_restore_are_absent_from_player_snapshot():
    player = PlayerState(RogueArcher())
    before = player.snapshot()

    player.create_battle_checkpoint()

    assert player.snapshot() == before
    assert "checkpoint" not in repr(player.snapshot()).lower()

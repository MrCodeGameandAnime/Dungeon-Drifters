from copy import deepcopy

import pytest

from app.content.catalog import create_drifter, get_drifter_spec
from app.game.game_state import GameState
from app.game.party_state import PartyState
from app.items.equipment import EquipmentInstance
from app.player.player_state import PlayerState


def _party_with_equipment_snapshot(instance):
    party = GameState(PlayerState(create_drifter("branoc"))).party_state
    snapshot = party.snapshot()
    snapshot["active_drifter_ids"] = ["branoc"]
    snapshot["equipment_instances"] = [instance]
    return PartyState.from_snapshot(
        snapshot,
        companions=party.companions,
        active_drifter_ids=("branoc",),
    )


def test_party_equipment_instance_round_trip_preserves_identity_and_security():
    equipment = EquipmentInstance.create(
        instance_id="00000000-0000-4000-8000-000000000101",
        definition_id="field_helm",
        source_id="floor_two_reward_01",
        secured=False,
        stat_bonuses={"constitution": 1},
    ).snapshot()

    restored = _party_with_equipment_snapshot(equipment)

    assert len(restored.equipment_instances) == 1
    assert restored.equipment_instances[0].snapshot() == equipment
    assert restored.snapshot()["equipment_instances"] == [equipment]


def test_game_clone_preserves_party_owned_equipment_instances():
    game = GameState(
        PlayerState(get_drifter_spec("branoc").create_character())
    )
    item = EquipmentInstance.from_snapshot(
        {
            "instance_id": "00000000-0000-4000-8000-000000000103",
            "definition_id": "field_helm",
            "source_id": "floor_two_reward_01",
            "secured": False,
            "stat_bonuses": {"constitution": 1},
            "rarity": "common",
            "upgrade_rank": 0,
            "modifier_slots": {},
        }
    )
    game.party_state.add_equipment_instance(item)

    clone = game.clone()

    assert clone.party_state.equipment_instances[0].snapshot() == item.snapshot()
    assert clone.party_state.equipment_instances[0] is not item


@pytest.mark.parametrize(
    "invalid",
    (
        {
            "instance_id": "00000000-0000-4000-8000-000000000102",
            "definition_id": "unknown_helm",
            "source_id": "floor_two_reward_01",
            "secured": False,
            "stat_bonuses": {"constitution": 1},
            "rarity": "common",
            "upgrade_rank": 0,
            "modifier_slots": {},
        },
        {
            "instance_id": "not-a-uuid",
            "definition_id": "field_helm",
            "source_id": "floor_two_reward_01",
            "secured": False,
            "stat_bonuses": {"constitution": 1},
            "rarity": "common",
            "upgrade_rank": 0,
            "modifier_slots": {},
        },
    ),
)
def test_party_rejects_unknown_or_malformed_equipment_instance(invalid):
    with pytest.raises(ValueError):
        _party_with_equipment_snapshot(deepcopy(invalid))

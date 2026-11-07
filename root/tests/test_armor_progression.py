import copy

from app.game.armor_progression import (
    ArmorProgressionService,
    ArmorProgressionStatus,
)
from app.content.armor_spec import get_armor_rarity
from app.persistence.save_document import build_save_document, reconstruct_game_state
from app.items.equipment import EquipmentInstance
from app.persistence.ports import SaveLoadResult
from app.persistence.save_port_contract import SaveLoadStatus
from tests.game_test_support import completed_hub_game


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


def _armor(*, secured=True, rarity="common", upgrade_rank=0):
    return EquipmentInstance.create(
        instance_id="00000000-0000-4000-8000-000000000411",
        definition_id="field_chest",
        source_id="floor_two_reward_01",
        secured=secured,
        stat_bonuses={"constitution": 2, "spirit": 1},
        rarity=rarity,
        upgrade_rank=upgrade_rank,
        modifier_slots={"I": "bastion_grade_i"},
    )


def _game_with_armor(*, secured=True, rarity="common", upgrade_rank=0):
    game = completed_hub_game()
    game.party_state.add_equipment_instance(
        _armor(secured=secured, rarity=rarity, upgrade_rank=upgrade_rank)
    )
    game._bind_equipment_state()
    return game


def test_stat_upgrade_is_deterministic_authored_and_preserves_instance():
    game = _game_with_armor()
    refs = game.player_state.equipped_equipment_ids
    refs["chest"] = "00000000-0000-4000-8000-000000000411"
    game.player_state._set_equipped_equipment_ids(refs)
    game._bind_equipment_state()
    game.party_state.add_shared_gold(1000)
    game.party_state.add_shared_items({"grade_i_metal": 10})
    save_port = MemorySavePort()
    service = ArmorProgressionService(save_port=save_port)
    before_gold = game.party_state.shared_gold
    before_hp = game.player_state.health.current
    before_max_hp = game.player_state.health.maximum
    before_permanent_constitution = game.player_state.stats.effective_stat(
        "constitution"
    )
    before_weapon = game.player_state.signature_weapon_state.snapshot()
    before_effects = game.player_state.combat_passive_effects
    original = game.party_state.equipment_instance(
        "00000000-0000-4000-8000-000000000411"
    )
    preview = service.preview_stat_upgrade(game, instance_id=original.instance_id)

    result = service.upgrade_stat(game, instance_id=original.instance_id)

    upgraded = result.game_state.party_state.equipment_instance(original.instance_id)
    assert result.status is ArmorProgressionStatus.UPGRADED
    assert preview.can_apply is True
    assert preview.gold_cost == 10
    assert (preview.material_id, preview.material_quantity) == ("grade_i_metal", 1)
    assert preview.projected_stat_bonuses == tuple(sorted(upgraded.stat_bonuses.items()))
    assert upgraded.instance_id == original.instance_id
    assert upgraded.upgrade_rank == 1
    assert upgraded.snapshot()["stat_bonuses"] == {"constitution": 2, "spirit": 1}
    assert upgraded.stat_bonuses == {"constitution": 3, "spirit": 1}
    assert result.game_state.party_state.shared_gold == before_gold - 10
    assert result.game_state.party_state.shared_items["grade_i_metal"] == 9
    assert result.game_state.player_state.health.current == before_hp
    assert result.game_state.player_state.health.maximum > before_max_hp
    assert result.game_state.player_state.stats.effective_stat("constitution") == (
        before_permanent_constitution
    )
    assert result.game_state.player_state.signature_weapon_state.snapshot() == (
        before_weapon
    )
    assert result.game_state.player_state.combat_passive_effects == before_effects
    assert len(save_port.saved_states) == 1
    restored = reconstruct_game_state(
        build_save_document(save_port.saved_states[0])
    )
    restored_item = restored.party_state.equipment_instance(original.instance_id)
    assert restored_item.snapshot() == upgraded.snapshot()
    assert restored.player_state.effective_stat("constitution") == (
        result.game_state.player_state.effective_stat("constitution")
    )


def test_stat_upgrade_track_caps_at_four_without_touching_other_state():
    game = _game_with_armor(upgrade_rank=4)
    before = copy.deepcopy(game.snapshot())
    save_port = MemorySavePort()

    result = ArmorProgressionService(save_port=save_port).upgrade_stat(
        game,
        instance_id="00000000-0000-4000-8000-000000000411",
    )

    assert result.status is ArmorProgressionStatus.MAX_RANK
    assert result.game_state is game
    assert game.snapshot() == before
    assert save_port.saved_states == []


def test_stat_upgrade_track_reaches_four_using_authored_grade_one_material():
    game = _game_with_armor()
    game.party_state.add_shared_gold(1000)
    game.party_state.add_shared_items({"grade_i_metal": 10})
    service = ArmorProgressionService(save_port=MemorySavePort())

    for expected_rank in range(1, 5):
        result = service.upgrade_stat(
            game,
            instance_id="00000000-0000-4000-8000-000000000411",
        )
        assert result.status is ArmorProgressionStatus.UPGRADED
        game = result.game_state
        item = game.party_state.equipment_instance(
            "00000000-0000-4000-8000-000000000411"
        )
        assert item.upgrade_rank == expected_rank

    assert item.stat_bonuses == {"constitution": 6, "spirit": 1}
    assert game.party_state.shared_items.get("grade_i_metal", 0) == 0
    assert service.upgrade_stat(game, instance_id=item.instance_id).status is (
        ArmorProgressionStatus.MAX_RANK
    )


def test_rarity_advancement_is_separate_and_preserves_investment_and_modifier():
    game = _game_with_armor(upgrade_rank=3)
    game.party_state.add_shared_gold(1000)
    game.party_state.add_shared_items({"grade_i_cores": 1})
    save_port = MemorySavePort()
    service = ArmorProgressionService(save_port=save_port)
    preview = service.preview_rarity_advance(
        game,
        instance_id="00000000-0000-4000-8000-000000000411",
    )

    result = service.advance_rarity(
        game,
        instance_id="00000000-0000-4000-8000-000000000411",
    )

    advanced = result.game_state.party_state.equipment_instance(
        "00000000-0000-4000-8000-000000000411"
    )
    assert result.status is ArmorProgressionStatus.RARITY_ADVANCED
    assert preview.can_apply is True
    assert preview.next_rarity == "uncommon"
    assert preview.projected_stat_bonuses == tuple(sorted(advanced.stat_bonuses.items()))
    assert advanced.rarity == "uncommon"
    assert advanced.upgrade_rank == 3
    assert advanced.modifier_slots == {"I": "bastion_grade_i"}
    assert advanced.stat_bonuses == {"constitution": 5, "spirit": 1}
    assert result.game_state.party_state.shared_items.get("grade_i_cores", 0) == 0
    assert result.game_state.party_state.shared_gold == game.party_state.shared_gold - 25
    assert len(save_port.saved_states) == 1


def test_rarity_path_unlocks_each_grade_in_order_without_randomness():
    game = _game_with_armor()
    game.party_state.add_shared_gold(10000)
    game.party_state.add_shared_items(
        {
            "grade_i_cores": 1,
            "grade_ii_cores": 1,
            "grade_iii_cores": 1,
            "grade_iv_cores": 1,
        }
    )
    service = ArmorProgressionService(save_port=MemorySavePort())
    expected = (
        ("uncommon", ("I", "II")),
        ("rare", ("I", "II", "III")),
        ("epic", ("I", "II", "III", "IV")),
        ("legendary", ("I", "II", "III", "IV", "V")),
    )

    for rarity, grades in expected:
        result = service.advance_rarity(
            game,
            instance_id="00000000-0000-4000-8000-000000000411",
        )
        assert result.status is ArmorProgressionStatus.RARITY_ADVANCED
        game = result.game_state
        armor = game.party_state.equipment_instance(
            "00000000-0000-4000-8000-000000000411"
        )
        assert armor.rarity == rarity
        assert armor.snapshot()["modifier_slots"] == {"I": "bastion_grade_i"}
        assert get_armor_rarity(armor.rarity).modifier_grades == grades

    before = copy.deepcopy(game.snapshot())
    assert service.advance_rarity(game, instance_id=armor.instance_id).status is (
        ArmorProgressionStatus.MAX_RARITY
    )
    assert game.snapshot() == before


def test_rarity_advance_save_failure_rolls_back_gold_material_and_item():
    game = _game_with_armor()
    game.party_state.add_shared_gold(100)
    game.party_state.add_shared_items({"grade_i_cores": 1})
    before = copy.deepcopy(game.snapshot())

    result = ArmorProgressionService(
        save_port=MemorySavePort(SaveLoadStatus.INVALID)
    ).advance_rarity(game, instance_id="00000000-0000-4000-8000-000000000411")

    assert result.status is ArmorProgressionStatus.SAVE_FAILED
    assert result.game_state is game
    assert game.snapshot() == before


def test_unsecured_or_failed_persistence_progression_has_no_partial_mutation():
    game = _game_with_armor(secured=False)
    game.party_state.add_shared_gold(100)
    game.party_state.add_shared_items({"grade_i_metal": 1})
    before = copy.deepcopy(game.snapshot())
    service = ArmorProgressionService(save_port=MemorySavePort())

    unsecured = service.upgrade_stat(
        game,
        instance_id="00000000-0000-4000-8000-000000000411",
    )
    assert unsecured.status is ArmorProgressionStatus.NOT_AVAILABLE
    assert game.snapshot() == before

    game = _game_with_armor()
    game.party_state.add_shared_gold(100)
    game.party_state.add_shared_items({"grade_i_metal": 1})
    before = copy.deepcopy(game.snapshot())
    failed = ArmorProgressionService(
        save_port=MemorySavePort(SaveLoadStatus.INVALID)
    ).upgrade_stat(game, instance_id="00000000-0000-4000-8000-000000000411")
    assert failed.status is ArmorProgressionStatus.SAVE_FAILED
    assert failed.game_state is game
    assert game.snapshot() == before


def test_insufficient_upgrade_and_rarity_resources_are_mutation_free():
    game = _game_with_armor()
    before = copy.deepcopy(game.snapshot())
    save_port = MemorySavePort()
    service = ArmorProgressionService(save_port=save_port)

    upgrade = service.upgrade_stat(
        game,
        instance_id="00000000-0000-4000-8000-000000000411",
    )
    rarity = service.advance_rarity(
        game,
        instance_id="00000000-0000-4000-8000-000000000411",
    )

    assert upgrade.status is ArmorProgressionStatus.INSUFFICIENT_RESOURCES
    assert rarity.status is ArmorProgressionStatus.INSUFFICIENT_RESOURCES
    assert not service.preview_stat_upgrade(
        game,
        instance_id="00000000-0000-4000-8000-000000000411",
    ).can_apply
    assert game.snapshot() == before
    assert save_port.saved_states == []


def test_static_accessories_cannot_be_upgraded_or_rarity_advanced():
    game = completed_hub_game()
    ring = EquipmentInstance.create(
        instance_id="00000000-0000-4000-8000-000000000412",
        definition_id="iron_ring",
        source_id="hub_initial_ring",
        secured=True,
        stat_bonuses={"intuition": 1},
    )
    game.party_state.add_equipment_instance(ring)
    game.party_state.add_shared_gold(1000)
    game.party_state.add_shared_items(
        {"grade_i_cores": 1, "grade_i_metal": 1}
    )
    before = copy.deepcopy(game.snapshot())
    service = ArmorProgressionService(save_port=MemorySavePort())

    upgrade = service.upgrade_stat(game, instance_id=ring.instance_id)
    advance = service.advance_rarity(game, instance_id=ring.instance_id)

    assert upgrade.status is ArmorProgressionStatus.NOT_ARMOR
    assert advance.status is ArmorProgressionStatus.NOT_ARMOR
    assert game.snapshot() == before

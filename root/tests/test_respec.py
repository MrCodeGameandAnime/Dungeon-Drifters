from types import SimpleNamespace

import pytest

from app.game.party_state import DungeonPhase
from app.game.respec import (
    REVISION_PARCHMENT_ITEM_ID,
    RespecService,
    RespecStatus,
)
from app.persistence.save_port_contract import SaveLoadStatus
from tests.game_test_support import completed_hub_game
from tests.persistence_test_support import make_test_save_port


class MemorySavePort:
    def __init__(self, status=SaveLoadStatus.SAVED):
        self.status = status
        self.calls = 0
        self.saved_state = None

    def inspect(self):
        return None

    def load(self):
        return None

    def save(self, game_state):
        self.calls += 1
        if self.status is SaveLoadStatus.SAVED:
            self.saved_state = game_state
        return SimpleNamespace(status=self.status)


def _build_purchased_drifter(player):
    player.gain_experience(player.level_state.next_threshold)
    player.gain_permanent_discovery_growth_points(5)
    player.increase_permanent_stat("constitution")
    player.purchase_advancement("branoc_p01")
    player.purchase_advancement("branoc_a01")
    player.equip_normal_move("branoc_a01", slot=2)


def _player_fingerprint(player):
    return {
        "stats": player.stats.as_dict(),
        "growth_points": player.growth_points,
        "discovery": player.permanent_discovery_bonuses,
        "advancement": player.advancement_state.snapshot(),
        "resources": (player.health.current, player.mana_resource.current),
        "weapon": player.signature_weapon_state.snapshot(),
    }


def test_preview_reports_exact_refund_and_does_not_mutate_the_game():
    game = completed_hub_game()
    branoc = game.member_for_drifter_id("branoc")
    _build_purchased_drifter(branoc)
    before = _player_fingerprint(branoc)

    preview = RespecService(save_port=MemorySavePort()).preview(game, "branoc")

    assert preview.drifter_id == "branoc"
    assert preview.revision_parchment_cost == 0
    assert preview.growth_points_refunded == 6
    assert preview.resulting_growth_points == 8
    assert preview.purchased_stat_points == (("constitution", 1),)
    assert preview.purchased_passive_skill_ids == ("branoc_p01",)
    assert preview.purchased_active_skill_ids == ("branoc_a01",)
    assert _player_fingerprint(branoc) == before


def test_first_respec_is_free_and_changes_only_the_selected_drifter():
    game = completed_hub_game()
    branoc = game.member_for_drifter_id("branoc")
    azhvielle = game.member_for_drifter_id("azhvielle")
    _build_purchased_drifter(branoc)
    other_before = _player_fingerprint(azhvielle)
    branoc.health.current = 10
    branoc.mana_resource.current = 7
    port = MemorySavePort()

    result = RespecService(save_port=port).respec(
        game,
        "branoc",
        confirmed=True,
    )

    reset = result.game_state.member_for_drifter_id("branoc")
    assert result.status is RespecStatus.RESPECCED
    assert result.preview.revision_parchment_cost == 0
    assert reset.growth_points == 8
    assert reset.stats.constitution == 14
    assert reset.purchased_passive_skill_ids == ()
    assert reset.purchased_active_skill_ids == ()
    assert reset.equipped_normal_move_ids == reset.advancement_state.starting_normal_move_ids
    assert reset.respec_count == 1
    assert reset.permanent_discovery_bonuses == {
        "max_hp": 0,
        "max_mana": 0,
        "growth_points_awarded": 5,
    }
    assert (reset.health.current, reset.mana_resource.current) == (10, 7)
    assert _player_fingerprint(
        result.game_state.member_for_drifter_id("azhvielle")
    ) == other_before
    assert result.game_state.party_state.shared_items == {}
    assert port.calls == 1


def test_respec_preserves_weapon_discovery_and_non_gp_loadout_state():
    game = completed_hub_game()
    branoc = game.player_state
    _build_purchased_drifter(branoc)
    starting_moves = branoc.advancement_state.starting_normal_move_ids
    branoc.equip_normal_move(starting_moves[1], slot=0)
    branoc.signature_weapon_state._learned_technique_ids.append("test_weapon_technique")
    branoc.signature_weapon_state.set_slot_progress("blade_guard", 25)
    branoc.increase_permanent_max_hp(10)
    branoc.increase_permanent_max_mana(5)
    game.world_state.claim_permanent_discovery("spirit_relic_test_01")
    weapon_before = branoc.signature_weapon_state.snapshot()
    discovery_before = branoc.permanent_discovery_bonuses
    claims_before = game.world_state.permanent_discovery_claims

    result = RespecService(save_port=MemorySavePort()).respec(
        game,
        "branoc",
        confirmed=True,
    )

    reset = result.game_state.player_state
    assert reset.equipped_normal_move_ids[0] == starting_moves[1]
    assert reset.equipped_normal_move_ids[2] == starting_moves[2]
    assert reset.signature_weapon_state.snapshot() == weapon_before
    assert reset.permanent_discovery_bonuses == discovery_before
    assert result.game_state.world_state.permanent_discovery_claims == claims_before


def test_respec_clamps_current_resources_to_recalculated_maxima():
    game = completed_hub_game()
    branoc = game.player_state
    branoc.gain_experience(branoc.level_state.next_threshold)
    branoc.increase_permanent_stat("constitution")
    branoc.increase_permanent_stat("spirit")
    branoc.health.current = branoc.health.maximum
    branoc.mana_resource.current = branoc.mana_resource.maximum
    old_health_max = branoc.health.maximum
    old_mana_max = branoc.mana_resource.maximum

    result = RespecService(save_port=MemorySavePort()).respec(
        game,
        "branoc",
        confirmed=True,
    )
    reset = result.game_state.player_state

    assert reset.health.maximum < old_health_max
    assert reset.mana_resource.maximum < old_mana_max
    assert reset.health.current == reset.health.maximum
    assert reset.mana_resource.current == reset.mana_resource.maximum


def test_each_drifter_has_an_independent_free_respec_and_repeats_need_parchment():
    game = completed_hub_game()
    port = MemorySavePort()
    service = RespecService(save_port=port)

    first = service.respec(game, "branoc", confirmed=True)
    second = service.respec(first.game_state, "azhvielle", confirmed=True)
    repeat_without_parchment = service.respec(
        second.game_state,
        "branoc",
        confirmed=True,
    )

    assert first.status is RespecStatus.RESPECCED
    assert second.status is RespecStatus.RESPECCED
    assert first.preview.revision_parchment_cost == 0
    assert second.preview.revision_parchment_cost == 0
    assert repeat_without_parchment.status is RespecStatus.INSUFFICIENT_PARCHMENT
    assert port.calls == 2
    assert repeat_without_parchment.game_state is second.game_state

    second.game_state.party_state.add_shared_items(
        {REVISION_PARCHMENT_ITEM_ID: 2}
    )
    cancelled_paid = service.respec(
        second.game_state,
        "branoc",
        confirmed=False,
    )
    assert cancelled_paid.status is RespecStatus.CANCELLED
    assert cancelled_paid.game_state.party_state.shared_items == {
        REVISION_PARCHMENT_ITEM_ID: 2
    }
    assert cancelled_paid.game_state.player_state.respec_count == 1

    repeat_with_parchment = service.respec(
        cancelled_paid.game_state,
        "branoc",
        confirmed=True,
    )
    assert repeat_with_parchment.status is RespecStatus.RESPECCED
    assert repeat_with_parchment.preview.revision_parchment_cost == 1
    assert repeat_with_parchment.game_state.party_state.shared_items == {
        REVISION_PARCHMENT_ITEM_ID: 1
    }


def test_cancel_invalid_target_and_non_hub_leave_state_and_save_untouched():
    game = completed_hub_game()
    port = MemorySavePort()
    service = RespecService(save_port=port)
    before = _player_fingerprint(game.player_state)

    cancelled = service.respec(game, "branoc", confirmed=False)
    invalid_target = service.respec(game, "zhaivra", confirmed=True)
    assert game.party_state.start_floor_one_run()
    outside_hub = service.respec(game, "branoc", confirmed=True)

    assert cancelled.status is RespecStatus.CANCELLED
    assert invalid_target.status is RespecStatus.INVALID_TARGET
    assert outside_hub.status is RespecStatus.NOT_AT_HUB
    assert _player_fingerprint(game.player_state) == before
    assert port.calls == 0
    assert game.party_state.phase is DungeonPhase.OUTING


def test_persistence_failure_does_not_consume_parchment_or_change_player():
    game = completed_hub_game()
    branoc = game.player_state
    _build_purchased_drifter(branoc)
    game.party_state.add_shared_items({REVISION_PARCHMENT_ITEM_ID: 1})
    before = _player_fingerprint(branoc)
    items_before = game.party_state.shared_items

    result = RespecService(
        save_port=MemorySavePort(SaveLoadStatus.INVALID)
    ).respec(game, "branoc", confirmed=True)

    assert result.status is RespecStatus.SAVE_FAILED
    assert result.game_state is game
    assert _player_fingerprint(branoc) == before
    assert game.party_state.shared_items == items_before


def test_respec_save_reload_preserves_history_and_never_duplicates_refund(tmp_path):
    game = completed_hub_game()
    branoc = game.player_state
    _build_purchased_drifter(branoc)
    port = make_test_save_port(tmp_path / "respec.json")
    service = RespecService(save_port=port)

    first = service.respec(game, "branoc", confirmed=True)
    loaded = port.load()
    assert loaded.status is SaveLoadStatus.LOADED
    restored = loaded.game_state.member_for_drifter_id("branoc")
    assert restored.growth_points == 8
    assert restored.respec_count == 1
    assert restored.purchased_stat_points == {
        "constitution": 0,
        "spirit": 0,
        "intelligence": 0,
        "strength": 0,
        "dexterity": 0,
        "intuition": 0,
    }

    repeated = service.respec(loaded.game_state, "branoc", confirmed=True)
    assert first.status is RespecStatus.RESPECCED
    assert repeated.status is RespecStatus.INSUFFICIENT_PARCHMENT
    assert repeated.game_state is loaded.game_state
    assert repeated.game_state.player_state.growth_points == 8


def test_respec_preview_rejects_non_boolean_confirmation():
    game = completed_hub_game()
    service = RespecService(save_port=MemorySavePort())

    with pytest.raises(TypeError, match="confirmed"):
        service.respec(game, "branoc", confirmed=1)


def test_respec_rejects_corrupt_stat_ledger_without_removing_base_stats():
    game = completed_hub_game()
    game.player_state.advancement_state._purchased_stat_points["strength"] = 1
    before = _player_fingerprint(game.player_state)
    service = RespecService(save_port=MemorySavePort())

    with pytest.raises(ValueError, match="exceed the current stat"):
        service.preview(game, "branoc")
    result = service.respec(game, "branoc", confirmed=True)

    assert result.status is RespecStatus.INVALID_TARGET
    assert result.game_state is game
    assert _player_fingerprint(game.player_state) == before

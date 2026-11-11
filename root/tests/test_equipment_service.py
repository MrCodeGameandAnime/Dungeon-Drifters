from app.game.equipment import EquipmentActionStatus, EquipmentService
from app.items.equipment import EquipmentInstance
from app.persistence.ports import SaveLoadResult
from app.persistence.save_port_contract import SaveLoadStatus
from app.content.catalog import get_route_spec
from app.content.route_spec import RouteNodeKind
from app.game.overworld_state import ContextualRoutePhase
from tests.game_test_support import (
    completed_hub_game,
    three_member_hub_game,
)


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


def _field_helm(*, secured=False):
    return EquipmentInstance.create(
        instance_id="00000000-0000-4000-8000-000000000201",
        definition_id="field_helm",
        source_id="floor_two_reward_01",
        secured=secured,
        stat_bonuses={"constitution": 1},
    )


def _three_member_floor_one_rest():
    game = three_member_hub_game()
    route = get_route_spec("floor_one")
    game.party_state.start_floor_one_run()
    game.overworld_state.begin_route(route.route_id)
    for node in route.nodes[1:]:
        game.overworld_state.advance_to(
            node.node_id,
            contextual_phase=(
                ContextualRoutePhase.ENTER_ENCOUNTER
                if node.encounter_id is not None
                else ContextualRoutePhase.NONE
            ),
        )
        if node.kind is RouteNodeKind.REST:
            return game, route, node
    raise AssertionError("Floor I has no Rest node")


def test_equipping_targets_exact_drifter_and_does_not_secure_or_heal():
    game = completed_hub_game()
    party = game.party_state
    item = _field_helm()
    party.add_equipment_instance(item)
    target = game.member_for_drifter_id("branoc")
    old_current_hp = target.health.current
    old_maximum_hp = target.health.maximum

    result = EquipmentService(save_port=MemorySavePort()).equip(
        game,
        target_drifter_id="branoc",
        instance_id=item.instance_id,
    )

    assert result.status is EquipmentActionStatus.EQUIPPED
    assert result.game_state.member_for_drifter_id(
        "branoc"
    ).equipped_equipment_ids["helm"] == item.instance_id
    assert result.game_state.member_for_drifter_id(
        "azhvielle"
    ).equipped_equipment_ids["helm"] is None
    equipped = result.game_state.party_state.equipment_instance(item.instance_id)
    assert equipped.secured is False
    updated_target = result.game_state.member_for_drifter_id("branoc")
    assert updated_target.health.maximum > old_maximum_hp
    assert updated_target.health.current == old_current_hp


def test_equipping_armor_does_not_consume_carried_supply_capacity():
    game = completed_hub_game()
    party = game.party_state
    party.add_shared_items({"healing_potion": 6})
    assert party.load_carried_supplies({"healing_potion": 6})
    item = _field_helm()
    party.add_equipment_instance(item)

    result = EquipmentService(save_port=MemorySavePort()).equip(
        game,
        target_drifter_id="branoc",
        instance_id=item.instance_id,
    )

    assert result.status is EquipmentActionStatus.EQUIPPED
    assert result.game_state.party_state.carried_item_units == 6
    assert result.game_state.party_state.carried_items == {"healing_potion": 6}
    assert result.game_state.party_state.equipment_instance(
        item.instance_id
    ).secured is False


def test_save_failure_leaves_original_equipment_and_stats_unchanged():
    game = completed_hub_game()
    item = _field_helm()
    game.party_state.add_equipment_instance(item)
    target = game.member_for_drifter_id("branoc")
    before_refs = target.equipped_equipment_ids
    before_stats = target.effective_stat("constitution")
    save_port = MemorySavePort(SaveLoadStatus.INVALID)

    result = EquipmentService(save_port=save_port).equip(
        game,
        target_drifter_id="branoc",
        instance_id=item.instance_id,
    )

    assert result.status is EquipmentActionStatus.SAVE_FAILED
    assert result.game_state is game
    assert target.equipped_equipment_ids == before_refs
    assert target.effective_stat("constitution") == before_stats
    assert game.party_state.equipment_instance(item.instance_id).secured is False
    assert save_port.saved_states == []


def test_equipping_owned_instance_transfers_it_between_exact_drifters():
    game = completed_hub_game()
    item = _field_helm()
    game.party_state.add_equipment_instance(item)
    service = EquipmentService(save_port=MemorySavePort())

    first = service.equip(
        game,
        target_drifter_id="branoc",
        instance_id=item.instance_id,
    )
    second = service.equip(
        first.game_state,
        target_drifter_id="azhvielle",
        instance_id=item.instance_id,
    )

    assert first.status is EquipmentActionStatus.EQUIPPED
    assert second.status is EquipmentActionStatus.EQUIPPED
    assert second.game_state.member_for_drifter_id(
        "branoc"
    ).equipped_equipment_ids["helm"] is None
    assert second.game_state.member_for_drifter_id(
        "azhvielle"
    ).equipped_equipment_ids["helm"] == item.instance_id
    assert len(second.game_state.party_state.equipment_instances) == 1


def test_replacing_same_slot_keeps_both_instances_party_owned():
    game = completed_hub_game()
    first_item = _field_helm()
    second_item = EquipmentInstance.create(
        instance_id="00000000-0000-4000-8000-000000000202",
        definition_id="field_helm",
        source_id="floor_two_reward_02",
        secured=False,
        stat_bonuses={"constitution": 1},
    )
    game.party_state.add_equipment_instance(first_item)
    game.party_state.add_equipment_instance(second_item)
    service = EquipmentService(save_port=MemorySavePort())

    first = service.equip(
        game, target_drifter_id="branoc", instance_id=first_item.instance_id
    )
    second = service.equip(
        first.game_state,
        target_drifter_id="branoc",
        instance_id=second_item.instance_id,
    )

    assert second.status is EquipmentActionStatus.EQUIPPED
    assert second.game_state.member_for_drifter_id(
        "branoc"
    ).equipped_equipment_ids["helm"] == second_item.instance_id
    assert {
        item.instance_id for item in second.game_state.party_state.equipment_instances
    } == {first_item.instance_id, second_item.instance_id}


def test_two_equipment_instances_can_be_swapped_between_recruited_drifters():
    game = completed_hub_game()
    branoc_helm = _field_helm()
    azhvielle_helm = EquipmentInstance.create(
        instance_id="00000000-0000-4000-8000-000000000204",
        definition_id="field_helm",
        source_id="floor_two_reward_04",
        secured=False,
        stat_bonuses={"constitution": 1},
    )
    game.party_state.add_equipment_instance(branoc_helm)
    game.party_state.add_equipment_instance(azhvielle_helm)
    service = EquipmentService(save_port=MemorySavePort())
    equipped_branoc = service.equip(
        game,
        target_drifter_id="branoc",
        instance_id=branoc_helm.instance_id,
    )
    equipped_azhvielle = service.equip(
        equipped_branoc.game_state,
        target_drifter_id="azhvielle",
        instance_id=azhvielle_helm.instance_id,
    )
    moved_branoc = service.equip(
        equipped_azhvielle.game_state,
        target_drifter_id="azhvielle",
        instance_id=branoc_helm.instance_id,
    )
    swapped = service.equip(
        moved_branoc.game_state,
        target_drifter_id="branoc",
        instance_id=azhvielle_helm.instance_id,
    )

    assert swapped.status is EquipmentActionStatus.EQUIPPED
    assert swapped.game_state.member_for_drifter_id(
        "branoc"
    ).equipped_equipment_ids["helm"] == azhvielle_helm.instance_id
    assert swapped.game_state.member_for_drifter_id(
        "azhvielle"
    ).equipped_equipment_ids["helm"] == branoc_helm.instance_id
    assert len(swapped.game_state.party_state.equipment_instances) == 2


def test_replacing_resource_bonus_clamps_current_health_without_healing():
    game = completed_hub_game()
    powered = _field_helm()
    plain = EquipmentInstance.create(
        instance_id="00000000-0000-4000-8000-000000000203",
        definition_id="field_helm",
        source_id="floor_two_reward_03",
        secured=False,
        stat_bonuses={},
    )
    game.party_state.add_equipment_instance(powered)
    game.party_state.add_equipment_instance(plain)
    service = EquipmentService(save_port=MemorySavePort())
    equipped = service.equip(
        game, target_drifter_id="branoc", instance_id=powered.instance_id
    )
    target = equipped.game_state.member_for_drifter_id("branoc")
    target.health.current = target.health.maximum

    replaced = service.equip(
        equipped.game_state,
        target_drifter_id="branoc",
        instance_id=plain.instance_id,
    )

    updated = replaced.game_state.member_for_drifter_id("branoc")
    assert replaced.status is EquipmentActionStatus.EQUIPPED
    assert updated.health.maximum < target.health.maximum
    assert updated.health.current == updated.health.maximum


def test_benched_recruited_drifter_can_manage_equipment_at_safe_rest():
    game, _, _ = _three_member_floor_one_rest()
    item = _field_helm()
    game.party_state.add_equipment_instance(item)

    result = EquipmentService(save_port=MemorySavePort()).equip(
        game, target_drifter_id="joruun", instance_id=item.instance_id
    )

    assert result.status is EquipmentActionStatus.EQUIPPED
    assert result.game_state.member_for_drifter_id(
        "joruun"
    ).equipped_equipment_ids["helm"] == item.instance_id


def test_floor_one_equipment_change_outside_saveable_rest_is_rejected_without_save():
    game = completed_hub_game()
    assert game.party_state.start_floor_one_run() == 100
    game.overworld_state.begin_route("floor_one")
    item = _field_helm()
    game.party_state.add_equipment_instance(item)
    save_port = MemorySavePort()
    before = game.snapshot()

    result = EquipmentService(save_port=save_port).equip(
        game,
        target_drifter_id="branoc",
        instance_id=item.instance_id,
    )

    assert result.status is EquipmentActionStatus.NOT_AVAILABLE
    assert result.game_state is game
    assert save_port.saved_states == []
    assert game.snapshot() == before


def test_active_pair_can_change_equipment_between_floor_two_encounters():
    game = completed_hub_game()
    assert game.party_state.start_floor_one_run() == 100
    assert game.party_state.complete_floor_one_boss(game.active_party_members)
    assert game.party_state.start_floor_two_run(
        run_id_factory=lambda: "equipment-run"
    ) == 100
    game.overworld_state.begin_route("floor_two")
    item = _field_helm()
    game.party_state.add_equipment_instance(item)

    result = EquipmentService(save_port=MemorySavePort()).equip(
        game,
        target_drifter_id="branoc",
        instance_id=item.instance_id,
    )

    assert result.status is EquipmentActionStatus.EQUIPPED
    assert result.game_state.member_for_drifter_id(
        "branoc"
    ).equipped_equipment_ids["helm"] == item.instance_id


def test_benched_recruited_drifter_cannot_change_loadout_after_rest():
    game, route, rest = _three_member_floor_one_rest()
    next_node = route.nodes[route.nodes.index(rest) + 1]
    game.overworld_state.record_resolved_rest_node(rest.node_id)
    game.overworld_state.advance_to(
        next_node.node_id,
        contextual_phase=ContextualRoutePhase.ENTER_ENCOUNTER,
    )
    item = _field_helm()
    game.party_state.add_equipment_instance(item)

    result = EquipmentService(save_port=MemorySavePort()).equip(
        game, target_drifter_id="joruun", instance_id=item.instance_id
    )

    assert result.status is EquipmentActionStatus.NOT_AVAILABLE
    assert result.game_state is game
    assert game.member_for_drifter_id(
        "joruun"
    ).equipped_equipment_ids["helm"] is None


def test_invalid_target_and_unowned_instance_are_mutation_free():
    game = completed_hub_game()
    item = _field_helm()
    before = game.snapshot()
    service = EquipmentService(save_port=MemorySavePort())

    invalid_target = service.equip(
        game, target_drifter_id="joruun", instance_id=item.instance_id
    )
    unowned_item = service.equip(
        game, target_drifter_id="branoc", instance_id=item.instance_id
    )

    assert invalid_target.status is EquipmentActionStatus.INVALID_TARGET
    assert unowned_item.status is EquipmentActionStatus.INVALID_INSTANCE
    assert game.snapshot() == before


def test_game_clone_preserves_equipped_equipment_reference_and_projection():
    game = completed_hub_game()
    item = _field_helm()
    game.party_state.add_equipment_instance(item)
    game.player_state._set_equipped_equipment_ids(
        {**game.player_state.equipped_equipment_ids, "helm": item.instance_id}
    )
    game._bind_equipment_state()

    clone = game.clone()

    assert clone.player_state.equipped_equipment_ids["helm"] == item.instance_id
    assert clone.player_state.effective_stat("constitution") == (
        game.player_state.effective_stat("constitution")
    )

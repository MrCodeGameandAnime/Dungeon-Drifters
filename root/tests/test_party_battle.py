import pytest
from types import SimpleNamespace

from app.combat.battle import Battle
from app.combat.resolver import CombatResolver
from app.content.catalog import (
    create_enemy_state,
    create_drifter,
    get_drifter_spec,
    get_encounter_spec,
)
from app.player.player_state import PlayerState
from app.presentation.battle_models import ActionIntent, BattleEventType
from app.ui.battle_ui import ChooseAction, ChooseHealingTarget, ChooseMove, GoBack
from tests.game_test_support import completed_hub_game


class StableRng:
    def __init__(self, *, pick="first"):
        self.pick = pick

    def randint(self, _minimum, _maximum):
        return 1

    def choice(self, values):
        return values[0] if self.pick == "first" else values[-1]


def player(drifter_id, dexterity):
    state = PlayerState(get_drifter_spec(drifter_id).create_character())
    state.character.dexterity = dexterity
    return state


def goblin(dexterity):
    state = create_enemy_state("goblin")
    state.permanent_stats.set_stat("dexterity", dexterity)
    return state


def defend(battle):
    return battle.submit(ChooseAction(ActionIntent.DEFEND))


def action_log(view):
    return tuple(
        (entry.actor_name, entry.action_name)
        for entry in view.log_entries
        if entry.event_type in {
            BattleEventType.DEFEND,
            BattleEventType.DAMAGE,
            BattleEventType.MISS,
        }
    )


def test_authored_tutorial_encounter_is_exactly_three_goblins():
    encounter = get_encounter_spec("dungeon_goblin_trio")

    assert encounter.enemy_archetype_ids == ("goblin", "goblin", "goblin")


def test_single_drifter_battle_does_not_allocate_party_turn_state():
    battle = Battle(player("branoc", 6), (goblin(5),), rng=StableRng())

    assert not hasattr(battle, "_party_members")
    assert not hasattr(battle, "_party_turn_queue")
    assert not hasattr(battle, "_party_dexterity_snapshot")
    assert battle.party == (battle.player_state,)


def test_party_battle_requires_player_states_with_unique_canonical_drifter_ids():
    lead = player("branoc", 6)

    with pytest.raises(TypeError, match="PlayerState"):
        Battle(
            lead,
            (goblin(1),),
            party=(SimpleNamespace(character=player("azhvielle", 4).character),),
            rng=StableRng(),
        )

    with pytest.raises(ValueError, match="Drifter IDs must be unique"):
        Battle(
            lead,
            (goblin(1),),
            party=(player("branoc", 4),),
            rng=StableRng(),
        )

    forged_profile = player("azhvielle", 4)
    forged_profile.character.profile = SimpleNamespace(drifter_id="azhvielle")
    with pytest.raises(ValueError, match="canonical Drifter profiles"):
        Battle(
            lead,
            (goblin(1),),
            party=(forged_profile,),
            rng=StableRng(),
        )

    unselected = PlayerState(create_drifter("azhvielle"))
    with pytest.raises(ValueError, match="canonical Drifter profiles"):
        Battle(
            lead,
            (goblin(1),),
            party=(unselected,),
            rng=StableRng(),
        )


def test_party_turns_project_and_resolve_each_drifters_own_combat_state():
    lead = player("branoc", 40)
    companion = player("zhaivra", 9)
    lead.super_resource.gain(23)
    companion.super_resource.gain(71)
    enemy = goblin(1)

    class RecordingResolver(CombatResolver):
        def __init__(self):
            super().__init__(rng=StableRng())
            self.calls = []

        def resolve_move(self, actor, target, move_name, **kwargs):
            self.calls.append((actor, move_name, kwargs))
            return super().resolve_move(actor, target, move_name, **kwargs)

    resolver = RecordingResolver()
    battle = Battle(
        lead,
        (enemy,),
        party=(companion,),
        resolver=resolver,
        rng=StableRng(),
    )

    lead_view = battle.current_view()
    assert lead_view.active_player_id == "drifter_branoc"
    assert lead_view.player.super_current == 23
    assert lead_view.super_meter.current == 23
    assert tuple(member.super_current for member in lead_view.party_members) == (
        23,
        71,
    )

    lead_moves = battle.submit(ChooseAction(ActionIntent.ATTACK))
    assert tuple(option.name for option in lead_moves.move_options) == tuple(
        move.name for move in lead.combat_moves if move.resource_type.value != "super"
    )
    companion_view = battle.submit(ChooseMove("Cinderlung Vesper"))

    assert companion_view.active_player_id == "drifter_zhaivra"
    assert companion_view.player.display_name == companion.display_name
    assert companion_view.player.super_current == 71
    assert companion_view.super_meter.current == 71
    assert companion_view.player.mana_current == companion.mana_resource.current
    items_view = battle.submit(ChooseAction(ActionIntent.ITEMS))
    assert {item.item_id for item in items_view.inventory_items} == {
        "ember_shard",
        "deep_coal",
        "night_berry",
    }
    assert all(item.quantity == 1 for item in items_view.inventory_items)
    battle.submit(GoBack())

    companion_moves = battle.submit(ChooseAction(ActionIntent.ATTACK))
    assert tuple(option.name for option in companion_moves.move_options) == tuple(
        move.name
        for move in companion.combat_moves
        if move.resource_type.value != "super"
    )
    before_mana = companion.mana_resource.current
    battle.submit(ChooseMove("Hollowstring Trine"))

    assert lead.mana_resource.current == lead.mana_resource.maximum - 3
    assert companion.mana_resource.current == before_mana - 4
    assert resolver.calls[0][0] is lead
    assert resolver.calls[0][1] == "Cinderlung Vesper"
    assert resolver.calls[0][2]["character_run_state"] is lead.character_run_state
    assert resolver.calls[1][0] is companion
    assert resolver.calls[1][1] == "Hollowstring Trine"
    assert (
        resolver.calls[1][2]["character_run_state"]
        is companion.character_run_state
    )


def test_party_battle_healing_potion_targets_exact_member_and_consumes_actor_turn():
    game = completed_hub_game()
    lead, companion = game.active_party_members
    party_state = game.party_state
    party_state.add_shared_items({"healing_potion": 1})
    assert party_state.load_carried_supplies({"healing_potion": 1})
    assert party_state.start_floor_one_run() == 100
    companion.health.take_damage(80)
    before_hp = companion.health.current
    battle = Battle(
        lead,
        (goblin(1),),
        party=(companion,),
        party_state=party_state,
        rng=StableRng(),
    )

    action = next(
        option for option in battle.current_view().action_options
        if option.intent is ActionIntent.HEALING_POTION
    )
    assert action.enabled
    target_view = battle.submit(ChooseAction(ActionIntent.HEALING_POTION))
    assert target_view.interaction_phase.value == "healing_targets"
    assert tuple(option.target_id for option in target_view.healing_target_options) == (
        "drifter_azhvielle",
    )

    view = battle.submit(ChooseHealingTarget("drifter_azhvielle"))

    assert companion.health.current == before_hp + companion.health.maximum * 40 // 100
    assert party_state.carried_items == {}
    assert view.active_player_id == "drifter_azhvielle"
    assert any(
        entry.event_type is BattleEventType.HEALING
        and entry.actor_name == lead.display_name
        and entry.target_name == companion.display_name
        and entry.amount == companion.health.maximum * 40 // 100
        for entry in view.log_entries
    )


def test_party_battle_interleaves_individual_dexterity_order_and_projects_party():
    lead = player("branoc", 6)
    companion = player("azhvielle", 4)
    first_goblin = goblin(5)
    second_goblin = goblin(3)
    battle = Battle(
        lead,
        (first_goblin, second_goblin),
        party=(companion,),
        rng=StableRng(),
    )

    first_view = battle.current_view()
    second_view = defend(battle)
    third_view = defend(battle)

    assert first_view.active_player_id == "drifter_branoc"
    assert tuple(member.target_id for member in first_view.party_members) == (
        "drifter_branoc",
        "drifter_azhvielle",
    )
    assert tuple(member.display_name for member in first_view.party_members) == (
        "Ser Branoc",
        "Azhvielle",
    )
    assert first_view.party_members[0].active is True
    assert first_view.party_members[1].active is False
    assert first_view.party_members[0].hp_current == lead.health.maximum
    assert first_view.party_members[1].mana_current == companion.mana_resource.current
    assert second_view.active_player_id == "drifter_azhvielle"
    assert second_view.party_members[0].active is False
    assert second_view.party_members[1].active is True
    assert second_view.party_members[0].hp_current < first_view.party_members[0].hp_current
    assert third_view.party_members[0].hp_current == lead.health.current
    assert third_view.active_player_id == "drifter_branoc"
    assert action_log(second_view)[-2:] == (
        ("Ser Branoc", "Defend"),
        ("Goblin 1", "slash"),
    )
    assert action_log(third_view)[-2:] == (
        ("Azhvielle", "Defend"),
        ("Goblin 2", "slash"),
    )


@pytest.mark.parametrize(
    ("pick", "expected"),
    (("first", "drifter_branoc"), ("last", "drifter_azhvielle")),
)
def test_equal_dexterity_uses_injected_rng_for_party_turn_order(pick, expected):
    battle = Battle(
        player("branoc", 6),
        (goblin(1),),
        party=(player("azhvielle", 6),),
        rng=StableRng(pick=pick),
    )

    assert battle.current_view().active_player_id == expected


def test_dexterity_change_immediately_reranks_only_unacted_combatants():
    lead = player("branoc", 6)
    companion = player("azhvielle", 4)
    first_goblin = goblin(5)
    second_goblin = goblin(3)
    class LowerCompanionDexterityResolver(CombatResolver):
        def __init__(self):
            super().__init__(rng=StableRng())

        def resolve_defend(self, actor, combat_state):
            if actor is lead:
                companion.character.dexterity = 2
            return super().resolve_defend(actor, combat_state)

    battle = Battle(
        lead,
        (first_goblin, second_goblin),
        party=(companion,),
        rng=StableRng(),
    )
    battle.resolver = LowerCompanionDexterityResolver()

    first_view = battle.current_view()
    after_lead = defend(battle)

    assert first_view.active_player_id == "drifter_branoc"
    assert after_lead.active_player_id == "drifter_azhvielle"
    assert action_log(after_lead)[:3] == (
        ("Ser Branoc", "Defend"),
        ("Goblin 1", "slash"),
        ("Goblin 2", "slash"),
    )


def test_defeated_lead_does_not_end_battle_while_companion_lives():
    lead = player("branoc", 6)
    lead.health.take_damage(lead.health.current)
    companion = player("azhvielle", 4)
    battle = Battle(
        lead,
        (goblin(1),),
        party=(companion,),
        rng=StableRng(),
    )

    battle.current_view()
    view = defend(battle)

    assert battle.is_complete is False
    assert view.active_player_id == "drifter_azhvielle"
    assert view.party_members[0].hp_current == 0
    assert 0 < view.party_members[1].hp_current <= companion.health.maximum


def test_battle_ends_in_defeat_when_both_drifters_are_down():
    lead = player("branoc", 6)
    companion = player("azhvielle", 4)
    lead.health.take_damage(lead.health.current)
    companion.health.take_damage(companion.health.current)
    battle = Battle(
        lead,
        (goblin(1),),
        party=(companion,),
        rng=StableRng(),
    )

    view = battle.current_view()

    assert battle.is_complete is True
    assert battle.winner == "enemy"
    assert view.party_members[0].hp_current == 0
    assert view.party_members[1].hp_current == 0


def test_enemy_selects_only_living_drifters_for_its_target():
    lead = player("branoc", 1)
    lead.health.take_damage(lead.health.current)
    companion = player("azhvielle", 6)
    battle = Battle(
        lead,
        (goblin(5),),
        party=(companion,),
        rng=StableRng(),
    )

    battle.current_view()
    view = defend(battle)

    assert view.active_player_id == "drifter_azhvielle"
    assert any(
        entry.target_name == "Azhvielle"
        for entry in view.log_entries
        if entry.actor_name == "Goblin"
    )

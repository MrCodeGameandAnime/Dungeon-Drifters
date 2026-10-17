import pytest

from app.combat.battle import Battle
from app.combat.resolver import CombatResolver
from app.content.catalog import (
    create_enemy_state,
    get_drifter_spec,
    get_encounter_spec,
)
from app.player.player_state import PlayerState
from app.presentation.battle_models import ActionIntent, BattleEventType
from app.ui.battle_ui import ChooseAction


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

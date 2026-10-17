"""Lazily loaded Hub tutorial and extraction portion of the raw probe."""


_TUTORIAL_COMPOSITION = ("goblin", "goblin", "goblin")
_TUTORIAL_REWARDS = (120, 9)


def _recruit_companion(state):
    from app.game.party_state import DungeonPhase
    from app.presentation.overworld_models import OverworldAction, OverworldScreen
    from app.ui.overworld_ui import ChooseCompanion, ChooseOverworldAction

    game = state["route_game"]
    session = state["route_session"]
    if session.current_view().screen is not OverworldScreen.HUB:
        raise AssertionError("tutorial recruitment did not begin at the Hub")
    selection = session.submit(
        ChooseOverworldAction(OverworldAction.RECRUIT_COMPANION)
    )
    if selection.screen is not OverworldScreen.COMPANION_SELECTION:
        raise AssertionError("Hub did not open companion selection")
    ready = session.submit(ChooseCompanion("azhvielle"))
    if ready.screen is not OverworldScreen.PARTY_READY:
        raise AssertionError("companion recruitment did not ready the party")
    if game.party_state.phase is not DungeonPhase.PARTY_READY:
        raise AssertionError("recruitment did not enter PARTY_READY")
    if game.party_state.shared_gold != 10:
        raise AssertionError("recruitment did not spend 65 of the Hub's 75 gold")
    if tuple(
        member.character.profile.drifter_id
        for member in game.party_state.companions
    ) != ("azhvielle",):
        raise AssertionError("the tutorial companion was not recruited")
    if not any(
        option.action.value == "ready" and option.enabled
        for option in ready.options
    ):
        raise AssertionError("the recruited party was not offered Ready")


def _ready_party(state):
    from app.game.party_state import DungeonPhase
    from app.presentation.battle_models import BattleView
    from app.presentation.overworld_models import OverworldAction
    from app.ui.overworld_ui import ChooseOverworldAction

    game = state["route_game"]
    session = state["route_session"]
    members = (game.player_state,) + game.party_state.companions
    if len(members) != 2:
        raise AssertionError("tutorial did not have a two-Drifter party")
    for member in members:
        if not member.is_alive():
            raise AssertionError("a Drifter was not alive at tutorial start")
        if member.health.current == member.health.maximum:
            member.health.take_damage(1)
        if member.mana_resource.current == member.mana_resource.maximum:
            member.mana_resource.spend(1)
        if member.health.current == member.health.maximum:
            raise AssertionError("tutorial did not begin with injured Drifters")
        if member.mana_resource.current == member.mana_resource.maximum:
            raise AssertionError("tutorial did not begin with spent Mana")

    state["hub_tutorial_xp_before"] = tuple(
        member.exp_state.current for member in members
    )
    battle_view = session.submit(ChooseOverworldAction(OverworldAction.READY))
    if not isinstance(battle_view, BattleView):
        raise AssertionError("Ready did not enter the tutorial Battle")
    if game.party_state.phase is not DungeonPhase.OUTING:
        raise AssertionError("Ready did not begin the tutorial outing")
    if len(battle_view.party_members) != 2:
        raise AssertionError("tutorial BattleView omitted a Drifter")
    battle_factory = state["route_battle_factory"]
    if battle_factory.battle_compositions[-1] != _TUTORIAL_COMPOSITION:
        raise AssertionError("tutorial encounter was not three Goblins")
    state["hub_tutorial_battle_view"] = battle_view


def _complete_tutorial_battle(state, complete_battle):
    from app.presentation.overworld_models import OverworldScreen

    battle_view = state.pop("hub_tutorial_battle_view")
    extraction = complete_battle(battle_view)
    if extraction.screen is not OverworldScreen.EXTRACTION:
        raise AssertionError("tutorial victory did not open Extraction")


def _assert_extraction_pending(state):
    from app.game.party_state import DungeonPhase
    from app.presentation.overworld_models import OverworldAction, OverworldScreen

    game = state["route_game"]
    session = state["route_session"]
    view = session.current_view()
    if view.screen is not OverworldScreen.EXTRACTION:
        raise AssertionError("tutorial rewards were not presented at Extraction")
    if game.party_state.phase is not DungeonPhase.EXTRACTION:
        raise AssertionError("party did not enter the Extraction phase")
    if (
        view.outing_rewards.experience,
        view.outing_rewards.gold,
    ) != _TUTORIAL_REWARDS:
        raise AssertionError("tutorial Extraction rewards changed")
    if view.outing_rewards.items != ():
        raise AssertionError("tutorial unexpectedly offered item rewards")
    if game.party_state.shared_gold != 10:
        raise AssertionError("tutorial gold was banked before extraction")
    members = (game.player_state,) + game.party_state.companions
    if tuple(
        member.exp_state.current for member in members
    ) != state["hub_tutorial_xp_before"]:
        raise AssertionError("tutorial EXP was banked before extraction")
    enabled = tuple(
        option.action for option in view.options if option.enabled
    )
    if enabled != (OverworldAction.RETURN_TO_HUB,):
        raise AssertionError("Extraction did not offer only Return to Hub")


def _return_to_hub(state):
    from app.presentation.overworld_models import OverworldAction, OverworldScreen
    from app.ui.overworld_ui import ChooseOverworldAction

    returned = state["route_session"].submit(
        ChooseOverworldAction(OverworldAction.RETURN_TO_HUB)
    )
    if returned.screen is not OverworldScreen.HUB:
        raise AssertionError("Extraction did not return the party to the Hub")


def _assert_final_state(state):
    from app.game.party_state import DungeonPhase
    from app.presentation.overworld_models import OverworldScreen

    game = state["route_game"]
    session = state["route_session"]
    party = game.party_state
    members = (game.player_state,) + party.companions
    if party.phase is not DungeonPhase.HUB or not party.tutorial_complete:
        raise AssertionError("tutorial extraction did not complete at the Hub")
    if len(members) != 2:
        raise AssertionError("tutorial extraction changed party membership")
    if party.shared_gold != 19:
        raise AssertionError("tutorial gold was not secured exactly once")
    if party.shared_items != {}:
        raise AssertionError("tutorial unexpectedly secured items")
    if (party.outing_rewards.experience, party.outing_rewards.gold) != (0, 0):
        raise AssertionError("tutorial rewards remained pending after extraction")
    if tuple(
        member.exp_state.current - previous
        for member, previous in zip(members, state["hub_tutorial_xp_before"])
    ) != (60, 60):
        raise AssertionError("tutorial EXP was not split evenly on extraction")
    for member in members:
        if member.health.current != member.health.maximum:
            raise AssertionError("extraction did not fully restore HP")
        if member.mana_resource.current != member.mana_resource.maximum:
            raise AssertionError("extraction did not fully restore Mana")
    if session.active_battle is not None:
        raise AssertionError("tutorial Battle remained active after extraction")
    battle_factory = state["route_battle_factory"]
    if battle_factory.completed_count != len(battle_factory.battle_compositions):
        raise AssertionError("tutorial Battle was not completed exactly once")
    if battle_factory.battle_compositions[-1] != _TUTORIAL_COMPOSITION:
        raise AssertionError("tutorial Battle composition evidence changed")
    if session.current_view().screen is not OverworldScreen.HUB:
        raise AssertionError("final tutorial view did not remain at the Hub")


def run(state, complete_battle, run_stage):
    run_stage("HUB_RECRUITMENT", lambda: _recruit_companion(state))
    run_stage("HUB_READY", lambda: _ready_party(state))
    run_stage(
        "HUB_TUTORIAL_BATTLE",
        lambda: _complete_tutorial_battle(state, complete_battle),
    )
    run_stage("HUB_EXTRACTION", lambda: _assert_extraction_pending(state))
    run_stage("HUB_RETURN", lambda: _return_to_hub(state))
    run_stage("HUB_FINAL_STATE", lambda: _assert_final_state(state))

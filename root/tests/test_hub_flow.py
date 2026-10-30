import pytest

from app.combat.battle import Battle
from app.content.catalog import DRIFTER_SPECS, create_enemy_state, get_drifter_spec
from app.game.overworld_session import OverworldSession
from app.game.party_state import COMPANION_RECRUITMENT_COST, DungeonPhase
from app.player.player_state import PlayerState
from app.presentation.battle_models import ActionIntent
from app.presentation.battle_models import BattleView
from app.presentation.overworld_models import (
    OverworldAction,
    OverworldAvailabilityReason,
    OverworldScreen,
)
from app.presentation.overworld_presenter import OverworldPresenter
from app.ui.overworld_ui import (
    ChooseCompanion,
    ChooseCharacterTarget,
    ChooseMerchantDismantle,
    ChooseMerchantImprove,
    ChooseMerchantTarget,
    ChooseMerchantTierV,
    ChooseOverworldAction,
    ChoosePermanentStatIncrease,
)
from app.ui.battle_ui import ChooseAction
from tests.game_test_support import hub_game as game_at_hub


def make_session(game):
    return OverworldSession(
        game,
        battle_factory=lambda *_args, **_kwargs: None,
        enemy_factory=lambda *_args, **_kwargs: None,
    )


def enabled_actions(view):
    return tuple(option.action for option in view.options if option.enabled)


def test_hub_offers_recruitment_without_surface_route_actions():
    session = make_session(game_at_hub())

    view = session.current_view()

    assert view.screen is OverworldScreen.HUB
    assert view.location_label == "Floor 1 Hub"
    assert OverworldAction.RECRUIT_COMPANION in enabled_actions(view)
    assert view.contextual_route_option is None
    assert OverworldAction.ENTER_ENCOUNTER not in enabled_actions(view)
    assert OverworldAction.RETRY not in enabled_actions(view)


def test_hub_offers_merchant_navigation():
    session = make_session(game_at_hub())
    view = session.current_view()

    assert any(
        option.label == "Merchant" and option.enabled
        for option in view.options
    )

    merchant = session.submit(
        ChooseOverworldAction(OverworldAction.MERCHANT)
    )

    assert merchant.screen is OverworldScreen.MERCHANT
    assert getattr(merchant, "merchant", None) is not None


def test_merchant_dismantle_and_improvement_spend_shared_materials():
    game = game_at_hub()
    session = make_session(game)
    game.party_state.add_shared_items({"goblin_scrap": 1})
    session.submit(ChooseOverworldAction(OverworldAction.MERCHANT))

    dismantled = session.submit(
        ChooseMerchantDismantle("branoc", "goblin_scrap")
    )

    assert dismantled.screen is OverworldScreen.MERCHANT
    assert "goblin_scrap" not in game.party_state.shared_items
    assert sum(
        game.party_state.shared_items.get(item_id, 0)
        for item_id in (
            "grade_i_metal",
            "grade_i_fiber",
            "grade_i_timber",
        )
    ) in (1, 2)
    assert game.party_state.crafting_experience == 0

    metal_before = game.party_state.shared_items.get("grade_i_metal", 0)
    game.party_state.add_shared_items({"grade_i_metal": 1})
    improved = session.submit(
        ChooseMerchantImprove("branoc", "blade_guard")
    )

    assert improved.merchant.slots[0].progress > 0
    assert game.party_state.shared_items.get("grade_i_metal", 0) == metal_before
    assert game.party_state.crafting_experience == 20


def test_merchant_tier_v_action_uses_the_selected_drifter_and_spends_cost(
    monkeypatch,
):
    import app.randomness

    game = game_at_hub()
    player = game.player_state
    game.party_state.add_crafting_experience(990)
    for slot_id in player.signature_weapon_state.slot_progress:
        player.signature_weapon_state.set_slot_progress(slot_id, 100)
    costs = {
        "grade_iv_metal": 12,
        "grade_iv_fiber": 12,
        "grade_iv_timber": 12,
        "grade_iv_cores": 12,
    }
    game.party_state.add_shared_items(costs)
    monkeypatch.setattr(app.randomness, "randint", lambda _start, _end: 1)
    session = make_session(game)
    session.submit(ChooseOverworldAction(OverworldAction.MERCHANT))

    result = session.submit(ChooseMerchantTierV("branoc"))

    assert player.signature_weapon_state.tier_v_success is True
    assert game.party_state.shared_items == {}
    assert "succeeded" in result.notice


def test_merchant_target_selection_is_reflected_and_stale_targets_are_rejected():
    game = game_at_hub()
    lead = game.player_state
    companion = PlayerState(get_drifter_spec("azhvielle").create_character())
    assert game.party_state.recruit_companion(lead, companion)
    assert game.party_state.begin_outing()
    assert game.party_state.begin_extraction(experience=0, gold=0)
    assert game.party_state.complete_extraction((lead, companion))
    game.party_state.add_shared_items({"grade_i_metal": 1})
    session = make_session(game)
    session.submit(ChooseOverworldAction(OverworldAction.MERCHANT))

    selected = session.submit(ChooseMerchantTarget("azhvielle"))
    rejected = session.submit(ChooseMerchantImprove("branoc", "blade_guard"))

    assert selected.merchant.selected_target_id == "azhvielle"
    assert rejected.notice == "Choose that Drifter before using the merchant."
    assert game.party_state.shared_items == {"grade_i_metal": 1}
    assert game.player_state.signature_weapon_state.slot_progress["blade_guard"] == 0


def test_character_and_skills_can_inspect_and_grow_the_selected_companion():
    game = game_at_hub()
    lead = game.player_state
    companion = PlayerState(get_drifter_spec("joruun").create_character())
    assert game.party_state.recruit_companion(lead, companion)
    assert game.party_state.begin_outing()
    assert game.party_state.begin_extraction(experience=0, gold=0)
    assert game.party_state.complete_extraction((lead, companion))
    companion.gain_experience(100)
    session = make_session(game)

    session.submit(ChooseOverworldAction(OverworldAction.CHARACTER))
    selected = session.submit(ChooseCharacterTarget("joruun"))

    assert selected.character.selected_target_id == "joruun"
    assert selected.character.display_name == companion.character.full_display_name
    assert tuple(row.value for row in selected.character.stats) == tuple(
        companion.character.permanent_stats.as_dict()[name]
        for name in (
            "strength",
            "constitution",
            "intelligence",
            "spirit",
            "dexterity",
            "intuition",
        )
    )

    skills = session.submit(ChooseOverworldAction(OverworldAction.SKILLS))
    assert skills.skills.selected_target_id == "joruun"
    strength_before = companion.character.permanent_stats.strength
    lead_strength_before = lead.character.permanent_stats.strength
    changed = session.submit(ChoosePermanentStatIncrease("strength"))

    assert companion.character.permanent_stats.strength == strength_before + 1
    assert lead.character.permanent_stats.strength == lead_strength_before
    assert changed.skills.selected_target_id == "joruun"


def test_recruitment_lists_the_three_other_authored_drifters_and_fixed_cost():
    game = game_at_hub(lead_id="branoc")
    view = OverworldPresenter().build(
        game,
        screen=OverworldScreen.COMPANION_SELECTION,
    )

    assert view.shared_gold == 75
    assert view.recruitment_cost == COMPANION_RECRUITMENT_COST == 65
    assert tuple(choice.drifter_id for choice in view.companion_choices) == tuple(
        spec.drifter_id for spec in DRIFTER_SPECS if spec.drifter_id != "branoc"
    )
    assert all(choice.enabled for choice in view.companion_choices)
    assert all(choice.cost == 65 for choice in view.companion_choices)


@pytest.mark.parametrize(
    "lead_id",
    [spec.drifter_id for spec in DRIFTER_SPECS],
)
def test_recruitment_candidates_exclude_the_selected_lead(lead_id):
    game = game_at_hub(lead_id=lead_id)

    view = OverworldPresenter().build(
        game,
        screen=OverworldScreen.COMPANION_SELECTION,
    )

    assert len(view.companion_choices) == 3
    assert lead_id not in {choice.drifter_id for choice in view.companion_choices}


def test_recruitment_is_authoritative_and_ready_is_an_explicit_next_action():
    game = game_at_hub(lead_id="branoc")
    session = make_session(game)
    hub = session.current_view()

    selection = session.submit(
        ChooseOverworldAction(OverworldAction.RECRUIT_COMPANION)
    )
    assert selection.screen is OverworldScreen.COMPANION_SELECTION
    assert game.party_state.phase is DungeonPhase.HUB
    assert game.party_state.shared_gold == 75

    ready = session.submit(ChooseCompanion("azhvielle"))

    assert ready.screen is OverworldScreen.PARTY_READY
    assert ready.location_label == "Floor 1 Hub"
    assert game.party_state.phase is DungeonPhase.PARTY_READY
    assert tuple(member.character.profile.drifter_id for member in game.party_state.companions) == (
        "azhvielle",
    )
    assert game.party_state.shared_gold == 10
    assert enabled_actions(ready) == (
        OverworldAction.READY,
        OverworldAction.BACK,
    )
    assert OverworldAction.ENTER_ENCOUNTER not in enabled_actions(hub)


def test_stale_or_forged_companion_selection_is_rejected_without_mutation():
    game = game_at_hub()
    session = make_session(game)
    session.submit(ChooseOverworldAction(OverworldAction.RECRUIT_COMPANION))
    before = game.snapshot()

    rejected = session.submit(ChooseCompanion("not-a-drifter"))

    assert rejected.screen is OverworldScreen.COMPANION_SELECTION
    assert rejected.notice == "That Drifter is not available."
    assert game.snapshot() == before


def test_stale_selection_from_another_session_cannot_recruit_twice():
    game = game_at_hub()
    first = make_session(game)
    second = make_session(game)
    first.submit(ChooseOverworldAction(OverworldAction.RECRUIT_COMPANION))
    second.submit(ChooseOverworldAction(OverworldAction.RECRUIT_COMPANION))

    first.submit(ChooseCompanion("azhvielle"))
    before_stale_input = game.snapshot()
    stale = second.submit(ChooseCompanion("zhaivra"))

    assert stale.screen is OverworldScreen.HUB
    assert stale.notice == "That Drifter is not available."
    assert game.snapshot() == before_stale_input
    assert len(game.party_state.companions) == 1
    assert game.party_state.shared_gold == 10


def test_back_from_recruitment_returns_to_hub_and_old_choice_is_stale():
    game = game_at_hub()
    session = make_session(game)
    session.submit(ChooseOverworldAction(OverworldAction.RECRUIT_COMPANION))

    hub = session.submit(ChooseOverworldAction(OverworldAction.BACK))
    stale = session.submit(ChooseCompanion("azhvielle"))

    assert hub.screen is OverworldScreen.HUB
    assert stale.screen is OverworldScreen.HUB
    assert stale.notice == "That Drifter is not available."
    assert game.party_state.shared_gold == 75
    assert game.party_state.companions == ()


def test_unaffordable_recruitment_is_disabled_and_cannot_be_forged():
    game = game_at_hub(gold=64)
    session = make_session(game)
    session.submit(ChooseOverworldAction(OverworldAction.RECRUIT_COMPANION))
    view = session.current_view()
    before = game.snapshot()

    rejected = session.submit(ChooseCompanion("azhvielle"))

    assert view.shared_gold == 64
    assert all(not choice.enabled for choice in view.companion_choices)
    assert all(
        choice.disabled_reason
        is OverworldAvailabilityReason.INSUFFICIENT_SHARED_GOLD
        for choice in view.companion_choices
    )
    assert rejected.notice == "You need 65 shared gold to recruit a Drifter."
    assert game.snapshot() == before


def test_back_after_recruitment_preserves_the_pair_and_ready_action():
    game = game_at_hub()
    session = make_session(game)
    session.submit(ChooseOverworldAction(OverworldAction.RECRUIT_COMPANION))
    session.submit(ChooseCompanion("azhvielle"))

    hub = session.submit(ChooseOverworldAction(OverworldAction.BACK))

    assert hub.screen is OverworldScreen.HUB
    assert game.party_state.phase is DungeonPhase.PARTY_READY
    assert game.party_state.shared_gold == 10
    assert len(game.party_state.companions) == 1
    assert OverworldAction.READY in enabled_actions(hub)
    assert OverworldAction.RECRUIT_COMPANION not in enabled_actions(hub)

    resumed = make_session(game).current_view()
    assert resumed.screen is OverworldScreen.HUB
    assert OverworldAction.READY in enabled_actions(resumed)


@pytest.mark.parametrize(
    ("action", "screen"),
    [
        (OverworldAction.CHARACTER, OverworldScreen.CHARACTER),
        (OverworldAction.ITEMS, OverworldScreen.ITEMS),
        (OverworldAction.MAP, OverworldScreen.MAP),
        (OverworldAction.OPTIONS, OverworldScreen.OPTIONS),
    ],
)
@pytest.mark.parametrize("party_ready", [False, True])
def test_back_from_hub_menus_returns_to_hub(action, screen, party_ready):
    session = make_session(game_at_hub())
    if party_ready:
        session.submit(
            ChooseOverworldAction(OverworldAction.RECRUIT_COMPANION)
        )
        session.submit(ChooseCompanion("azhvielle"))
        session.submit(ChooseOverworldAction(OverworldAction.BACK))

    opened = session.submit(ChooseOverworldAction(action))
    returned = session.submit(ChooseOverworldAction(OverworldAction.BACK))

    assert opened.screen is screen
    assert returned.screen is OverworldScreen.HUB


def test_hub_rejects_route_and_battle_inputs_as_unoffered():
    game = game_at_hub()
    session = make_session(game)

    route_input = session.submit(
        ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER)
    )
    battle_input = session.submit(ChooseAction(ActionIntent.ATTACK))

    assert route_input.screen is OverworldScreen.HUB
    assert route_input.notice == "That option is not available."
    assert battle_input.screen is OverworldScreen.HUB
    assert session.active_battle is None
    assert game.party_state.phase is DungeonPhase.HUB


def test_ready_action_starts_the_two_drifter_tutorial_battle():
    game = game_at_hub()
    session = OverworldSession(
        game,
        battle_factory=Battle,
        enemy_factory=create_enemy_state,
    )
    session.submit(ChooseOverworldAction(OverworldAction.RECRUIT_COMPANION))
    session.submit(ChooseCompanion("azhvielle"))
    before_ready = session.current_view()

    battle_view = session.submit(
        ChooseOverworldAction(OverworldAction.READY)
    )

    assert OverworldAction.READY in enabled_actions(before_ready)
    assert isinstance(battle_view, BattleView)
    assert len(battle_view.party_members) == 2
    assert len(session.active_battle.enemies) == 3
    assert game.party_state.phase is DungeonPhase.OUTING


def test_terminal_recruitment_menu_shows_cost_and_accepts_a_numbered_choice():
    from app.ui.terminal_overworld_ui import TerminalOverworldUI

    game = game_at_hub()
    view = OverworldPresenter().build(
        game,
        screen=OverworldScreen.COMPANION_SELECTION,
    )
    output = []
    inputs = iter(("2",))
    ui = TerminalOverworldUI(
        input_func=lambda _prompt: next(inputs),
        output_func=output.append,
        width_provider=lambda: 80,
        interactive=False,
    )

    ui.render(view)
    selected = ui.read_input(view)

    assert any("Shared gold: 75" in line for line in output)
    assert any("65" in line for line in output)
    assert selected == ChooseCompanion(view.companion_choices[1].drifter_id)


def test_terminal_recruitment_back_returns_the_semantic_back_action():
    from app.ui.terminal_overworld_ui import TerminalOverworldUI

    view = OverworldPresenter().build(
        game_at_hub(),
        screen=OverworldScreen.COMPANION_SELECTION,
    )
    ui = TerminalOverworldUI(
        input_func=lambda _prompt: "b",
        output_func=lambda _message: None,
        width_provider=lambda: 80,
        interactive=False,
    )

    assert ui.read_input(view) == ChooseOverworldAction(OverworldAction.BACK)

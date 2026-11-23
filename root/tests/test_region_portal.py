import copy

from app.combat.battle import Battle
from app.content.catalog import create_enemy_state, DRIFTER_SPECS
from app.game.overworld_session import OverworldSession
from app.game.story_state import KnowledgeStatus
from app.persistence.ports import SaveLoadResult
from app.persistence.save_document import build_save_document, reconstruct_game_state
from app.persistence.save_port_contract import SaveLoadStatus
from app.presentation.overworld_models import OverworldAction, OverworldScreen
from app.ui.overworld_ui import (
    ChooseDestination,
    ChooseOverworldAction,
    ChooseRegion,
)
from tests.game_test_support import completed_hub_game
from tests.persistence_test_support import make_test_save_port
from app.player.player_state import PlayerState


class StableRng:
    def randint(self, _minimum, _maximum):
        return 1

    def choice(self, values):
        return values[0]


class CountingSavePort:
    def __init__(self, delegate):
        self.delegate = delegate
        self.save_calls = 0

    def inspect(self):
        return self.delegate.inspect()

    def load(self):
        return self.delegate.load()

    def save(self, game_state):
        self.save_calls += 1
        return self.delegate.save(game_state)


class FailedSavePort:
    def inspect(self):
        return SaveLoadResult(SaveLoadStatus.MISSING)

    def load(self):
        return SaveLoadResult(SaveLoadStatus.MISSING)

    def save(self, _game_state):
        return SaveLoadResult(
            SaveLoadStatus.INVALID,
            error="injected write failure",
        )


def _make_session(game, save_port):
    return OverworldSession(
        game,
        battle_factory=lambda player, enemies, **kwargs: Battle(
            player,
            enemies,
            rng=StableRng(),
            **kwargs,
        ),
        enemy_factory=create_enemy_state,
        save_port=save_port,
    )


def _four_member_floor_three_clear():
    game = completed_hub_game()
    recruited_ids = {
        member.character.profile.drifter_id for member in game.recruited_members
    }
    for profile in DRIFTER_SPECS:
        if profile.drifter_id not in recruited_ids:
            assert game.party_state.recruit_companion(
                game.player_state,
                PlayerState(profile.create_character()),
                cost=0,
            )
    game.party_state._floor_one_cleared = True
    game.party_state._floor_two_cleared = True
    game.party_state._floor_three_cleared = True
    return game


def test_region_portal_starts_an_existing_destination_through_current_flow(tmp_path):
    game = completed_hub_game()
    session = _make_session(game, make_test_save_port(tmp_path / "portal.json"))

    hub = session.current_view()
    assert any(option.action is OverworldAction.REGION_PORTAL for option in hub.options)

    portal = session.submit(
        ChooseOverworldAction(OverworldAction.REGION_PORTAL)
    )
    assert portal.screen is OverworldScreen.REGION_PORTAL
    assert tuple(choice.region_id for choice in portal.region_choices) == ("region_1",)

    destinations = session.submit(ChooseRegion("region_1"))
    assert destinations.screen is OverworldScreen.REGION_DESTINATIONS
    floor_one = next(
        choice
        for choice in destinations.destination_choices
        if choice.destination_id == "floor_one"
    )
    assert floor_one.enabled

    warning = session.submit(ChooseDestination("floor_one"))
    assert warning.screen is OverworldScreen.FLOOR_ONE_WARNING


def test_hidden_region_or_destination_submissions_do_not_promote_knowledge(tmp_path):
    game = completed_hub_game()
    session = _make_session(game, make_test_save_port(tmp_path / "hidden.json"))
    session.submit(ChooseOverworldAction(OverworldAction.REGION_PORTAL))

    rejected = session.submit(ChooseRegion("region_2"))
    assert rejected.screen is OverworldScreen.REGION_PORTAL
    assert game.story_state.knowledge_status(
        "m8_fact_drowned_reliquary"
    ) is KnowledgeStatus.UNKNOWN

    session.submit(ChooseRegion("region_1"))
    before = game.story_state.snapshot()
    rejected_destination = session.submit(ChooseDestination("drowned_reliquary"))

    assert rejected_destination.screen is OverworldScreen.REGION_DESTINATIONS
    assert game.story_state.snapshot() == before


def test_drowned_briefing_persists_rumor_once_and_survives_reload(tmp_path):
    game = _four_member_floor_three_clear()
    delegate = make_test_save_port(tmp_path / "briefing.json")
    save_port = CountingSavePort(delegate)
    session = _make_session(game, save_port)

    briefing = session.submit(
        ChooseOverworldAction(OverworldAction.DROWNED_RELIQUARY_BRIEFING)
    )

    assert briefing.screen is OverworldScreen.HUB
    assert game.story_state.knowledge_status(
        "m8_fact_drowned_reliquary"
    ) is KnowledgeStatus.RUMORED
    assert "rumor" in briefing.adventure_text.lower()
    assert save_port.save_calls == 1
    loaded = delegate.load().game_state
    assert loaded.story_state.knowledge_status(
        "m8_fact_drowned_reliquary"
    ) is KnowledgeStatus.RUMORED
    assert "m8_drowned_reliquary_briefing" in loaded.story_state.completed_events

    repeated = session.submit(
        ChooseOverworldAction(OverworldAction.DROWNED_RELIQUARY_BRIEFING)
    )
    assert save_port.save_calls == 1
    assert game.story_state.knowledge_status(
        "m8_fact_drowned_reliquary"
    ) is KnowledgeStatus.RUMORED
    assert "not available" in repeated.notice.lower()


def test_migrated_floor_three_save_can_complete_briefing_through_hub(tmp_path):
    game = _four_member_floor_three_clear()
    historical = build_save_document(game)
    historical["schema_version"] = 25
    for field in (
        "floor_four_cleared",
        "floor_five_cleared",
        "region_two_unlocked",
    ):
        historical["party"].pop(field)
    historical["story"].pop("knowledge_facts")
    original = copy.deepcopy(historical)
    migrated_game = reconstruct_game_state(historical)

    assert historical == original
    assert migrated_game.party_state.floor_three_cleared
    assert len(migrated_game.recruited_members) == 4
    assert migrated_game.story_state.knowledge_status(
        "m8_fact_drowned_reliquary"
    ) is KnowledgeStatus.UNKNOWN

    delegate = make_test_save_port(tmp_path / "migrated-briefing.json")
    session = _make_session(migrated_game, delegate)
    hub = session.current_view()
    assert any(
        option.action is OverworldAction.DROWNED_RELIQUARY_BRIEFING
        for option in hub.options
    )
    briefing = session.submit(
        ChooseOverworldAction(OverworldAction.DROWNED_RELIQUARY_BRIEFING)
    )

    assert briefing.screen is OverworldScreen.HUB
    assert migrated_game.story_state.knowledge_status(
        "m8_fact_drowned_reliquary"
    ) is KnowledgeStatus.RUMORED
    reloaded = delegate.load().game_state
    assert reloaded.story_state.knowledge_status(
        "m8_fact_drowned_reliquary"
    ) is KnowledgeStatus.RUMORED

    portal = session.submit(
        ChooseOverworldAction(OverworldAction.REGION_PORTAL)
    )
    assert portal.screen is OverworldScreen.REGION_PORTAL
    destinations = session.submit(ChooseRegion("region_1"))
    assert next(
        choice
        for choice in destinations.destination_choices
        if choice.destination_id == "drowned_reliquary"
    ).knowledge_status == KnowledgeStatus.RUMORED.value
    assert {fact.fact_id for fact in destinations.knowledge_facts} == {
        "m8_fact_drowned_reliquary",
    }


def test_unlocked_region_two_is_visible_but_cannot_be_selected_without_routes():
    game = completed_hub_game()
    game.party_state._floor_one_cleared = True
    game.party_state._floor_two_cleared = True
    game.party_state._floor_three_cleared = True
    for profile in DRIFTER_SPECS:
        if profile.drifter_id in {
            member.character.profile.drifter_id
            for member in game.recruited_members
        }:
            continue
        assert game.party_state.recruit_companion(
            game.player_state,
            PlayerState(profile.create_character()),
            cost=0,
        )
    game.party_state._floor_four_cleared = True
    assert game.party_state.record_floor_five_clear()
    assert game.party_state.unlock_region_two()
    session = _make_session(game, FailedSavePort())
    session.submit(ChooseOverworldAction(OverworldAction.REGION_PORTAL))
    portal = session.current_view()
    region_two = next(
        choice for choice in portal.region_choices if choice.region_id == "region_2"
    )

    assert region_two.unlocked
    assert not region_two.selectable
    rejected = session.submit(ChooseRegion("region_2"))
    assert rejected.screen is OverworldScreen.REGION_PORTAL
    assert "no playable" in rejected.notice.lower()


def test_failed_briefing_save_keeps_event_and_knowledge_unpublished():
    game = _four_member_floor_three_clear()
    session = _make_session(game, FailedSavePort())
    before = game.story_state.snapshot()

    failed = session.submit(
        ChooseOverworldAction(OverworldAction.DROWNED_RELIQUARY_BRIEFING)
    )

    assert session.game_state is game
    assert game.story_state.snapshot() == before
    assert game.story_state.knowledge_status(
        "m8_fact_drowned_reliquary"
    ) is KnowledgeStatus.UNKNOWN
    assert "could not be saved" in failed.notice.lower()
    assert "rumor" not in failed.adventure_text.lower()


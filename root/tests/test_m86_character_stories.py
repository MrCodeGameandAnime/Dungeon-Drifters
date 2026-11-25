from copy import deepcopy

import pytest

from app.combat.battle import Battle
from app.content.catalog import create_enemy_state, get_drifter_spec, get_route_spec
from app.content.m8_story_scenes import M8_STORY_SCENES
from app.content.route_spec import RouteNodeKind
from app.game.game_state import GameState
from app.game.overworld_session import OverworldSession
from app.game.overworld_state import ContextualRoutePhase
from app.game.story_state import KnowledgeStatus
from app.persistence.ports import SaveLoadResult
from app.persistence.save_document import (
    build_save_document,
    reconstruct_game_state,
    validate_profile_payload,
    validate_save_document,
)
from app.persistence.save_port_contract import SaveLoadStatus
from app.player.player_state import PlayerState
from app.presentation.overworld_models import OverworldAction, OverworldScreen
from app.ui.overworld_ui import ChooseOverworldAction
from tests.game_test_support import completed_hub_game


class StableRng:
    def randint(self, minimum, maximum):
        return minimum

    def choice(self, values):
        return values[0]


class RecordingSavePort:
    def __init__(self, *, fail=False):
        self.fail = fail
        self.saved_state = None
        self.save_calls = 0

    def inspect(self):
        return SaveLoadResult(SaveLoadStatus.MISSING)

    def load(self):
        return self.inspect()

    def save(self, game_state):
        self.save_calls += 1
        if self.fail:
            return SaveLoadResult(SaveLoadStatus.INVALID)
        self.saved_state = game_state.clone()
        return SaveLoadResult(SaveLoadStatus.SAVED)


PAIR_SCENES = (
    (("branoc", "azhvielle"), "m8_pair_scene_branoc_azhvielle"),
    (("branoc", "joruun"), "m8_pair_scene_branoc_joruun"),
    (("branoc", "zhaivra"), "m8_pair_scene_branoc_zhaivra"),
    (("azhvielle", "joruun"), "m8_pair_scene_azhvielle_joruun"),
    (("azhvielle", "zhaivra"), "m8_pair_scene_azhvielle_zhaivra"),
    (("joruun", "zhaivra"), "m8_pair_scene_joruun_zhaivra"),
)
APPROVED_SCENE_IDS = {
    scene_id for _pair, scene_id in PAIR_SCENES
} | {
    "m8_azh_archive_memory",
    "m8_reliquary_echo_scene",
}


def _floor_four_midpoint_game(active_pair):
    game = completed_hub_game()
    recruited = {
        member.character.profile.drifter_id for member in game.recruited_members
    }
    for drifter_id in ("joruun", "zhaivra"):
        if drifter_id not in recruited:
            companion = PlayerState(get_drifter_spec(drifter_id).create_character())
            assert game.party_state.recruit_companion(
                game.player_state,
                companion,
                cost=0,
            )
    game.party_state._floor_one_cleared = True
    game.party_state._floor_two_cleared = True
    game.party_state._floor_three_cleared = True
    game.party_state.select_active_pair(
        active_pair,
        recruited_ids=tuple(
            member.character.profile.drifter_id
            for member in game.recruited_members
        ),
    )
    game.party_state.start_floor_four_run(
        run_id_factory=lambda: "m86-midpoint-run"
    )
    game.overworld_state.begin_route("floor_four")
    route = get_route_spec("floor_four")
    for node in route.nodes[1:6]:
        game.overworld_state.advance_to(
            node.node_id,
            contextual_phase=(
                ContextualRoutePhase.ENTER_ENCOUNTER
                if node.encounter_id is not None
                else ContextualRoutePhase.NONE
            ),
        )
    game.party_state._mark_encounter_progress()
    return game


def _session(game, save_port=None):
    return OverworldSession(
        game,
        battle_factory=lambda player, enemies, **kwargs: Battle(
            player,
            enemies,
            rng=StableRng(),
            **kwargs,
        ),
        enemy_factory=create_enemy_state,
        save_port=save_port or RecordingSavePort(),
        run_event_rng=StableRng(),
    )


def test_authored_story_content_preserves_approved_ids_and_lore_corrections():
    scenes = {scene.scene_id: scene for scene in M8_STORY_SCENES}
    assert set(scenes) == APPROVED_SCENE_IDS

    archive_text = " ".join(scenes["m8_azh_archive_memory"].dialogue).lower()
    assert "ashen regent" in archive_text
    assert "my name" in archive_text
    assert "removed a name" not in archive_text
    assert "crossed out" not in archive_text

    azh_zhaivra_text = " ".join(
        scenes["m8_pair_scene_azhvielle_zhaivra"].dialogue
    ).lower()
    assert "nhal voryss still lives" in azh_zhaivra_text
    assert "first turning" in azh_zhaivra_text
    assert "lost" not in azh_zhaivra_text

    faith_text = " ".join(
        scenes["m8_pair_scene_azhvielle_joruun"].dialogue
    ).lower()
    assert "i can pray" in faith_text
    assert "invoking holy magic" in faith_text

    echo_text = " ".join(
        scenes["m8_reliquary_echo_scene"].dialogue
    ).lower()
    assert "two expedition members" in echo_text
    assert "i heard" not in echo_text
    assert "i saw" not in echo_text


def test_existing_story_state_round_trips_through_schema_28_without_new_migration():
    game = completed_hub_game()
    game.story_state.complete_event("m8_drowned_reliquary_briefing")
    game.story_state.record_decision("legacy_story_choice", "share_warning")
    historical = build_save_document(game)
    historical["schema_version"] = 28
    original = deepcopy(historical)

    assert validate_profile_payload(historical) == original
    migrated = validate_save_document(historical)
    restored = reconstruct_game_state(historical)

    assert historical == original
    assert migrated["schema_version"] == 29
    assert migrated["story"]["completed_events"] == [
        "m8_drowned_reliquary_briefing"
    ]
    assert migrated["story"]["player_decisions"] == {
        "legacy_story_choice": "share_warning"
    }
    assert build_save_document(restored) == migrated


@pytest.mark.parametrize(
    ("pair", "scene_id"),
    tuple(
        (active_pair, scene_id)
        for pair, scene_id in PAIR_SCENES
        for active_pair in (pair, tuple(reversed(pair)))
    ),
)
def test_pair_scene_uses_active_pair_identity_independent_of_selection_order(
    pair,
    scene_id,
):
    session = _session(_floor_four_midpoint_game(pair))

    rest_view = session.current_view()
    assert rest_view.screen is OverworldScreen.REST
    assert OverworldAction.OPEN_PAIR_STORY in {
        option.action for option in rest_view.options
    }

    story_view = session.submit(
        ChooseOverworldAction(OverworldAction.OPEN_PAIR_STORY)
    )

    assert story_view.screen is OverworldScreen.STORY_SCENE
    assert session._active_story_scene_id == scene_id
    assert all(
        drifter_id in story_view.adventure_text.lower()
        for drifter_id in pair
    )
    assert story_view.options


def test_pair_scene_choice_is_saved_once_and_survives_reload():
    game = _floor_four_midpoint_game(("branoc", "azhvielle"))
    port = RecordingSavePort()
    session = _session(game, port)
    session.submit(ChooseOverworldAction(OverworldAction.OPEN_PAIR_STORY))

    response = session.submit(
        ChooseOverworldAction(OverworldAction.STORY_CHOICE_ONE)
    )

    event_id = "m8_pair_scene_branoc_azhvielle"
    assert response.screen is OverworldScreen.STORY_SCENE
    assert "warning" in response.adventure_text.lower()
    assert event_id in session.game_state.story_state.completed_events
    assert session.game_state.story_state.player_decisions[
        f"m8_story_choice_{event_id}"
    ] == "share_warning"
    assert port.save_calls == 1

    completed = session.submit(ChooseOverworldAction(OverworldAction.BACK))
    assert completed.screen is OverworldScreen.REST

    reloaded = reconstruct_game_state(build_save_document(session.game_state))
    restored_session = _session(reloaded, RecordingSavePort())
    assert OverworldAction.OPEN_PAIR_STORY not in {
        option.action for option in restored_session.current_view().options
    }
    assert reloaded.story_state.completed_events.count(event_id) == 1
    assert reloaded.story_state.player_decisions[
        f"m8_story_choice_{event_id}"
    ] == "share_warning"


def test_cancelling_pair_scene_records_nothing_and_returns_to_rest():
    game = _floor_four_midpoint_game(("branoc", "joruun"))
    session = _session(game)
    before = game.snapshot()
    session.submit(ChooseOverworldAction(OverworldAction.OPEN_PAIR_STORY))

    cancelled = session.submit(ChooseOverworldAction(OverworldAction.CANCEL))

    assert cancelled.screen is OverworldScreen.REST
    assert session.game_state.snapshot() == before
    assert not any(
        event.startswith("m8_pair_scene_")
        for event in session.game_state.story_state.completed_events
    )


def test_failed_archive_memory_save_keeps_fact_and_event_uncommitted_then_retries():
    game = _floor_four_midpoint_game(("azhvielle", "joruun"))
    port = RecordingSavePort(fail=True)
    session = _session(game, port)
    before = session.game_state.snapshot()
    rest_view = session.current_view()
    assert OverworldAction.OPEN_ARCHIVE_MEMORY in {
        option.action for option in rest_view.options
    }

    session.submit(ChooseOverworldAction(OverworldAction.OPEN_ARCHIVE_MEMORY))
    failed = session.submit(
        ChooseOverworldAction(OverworldAction.STORY_CONTINUE)
    )

    assert failed.screen is OverworldScreen.STORY_SCENE
    assert session.game_state.snapshot() == before
    assert "m8_azh_archive_memory" not in session.game_state.story_state.completed_events
    assert session.game_state.story_state.knowledge_status(
        "m8_fact_ashen_regent"
    ) is KnowledgeStatus.UNKNOWN

    port.fail = False
    session.submit(ChooseOverworldAction(OverworldAction.STORY_CONTINUE))
    assert session.game_state.story_state.completed_events.count(
        "m8_azh_archive_memory"
    ) == 1
    assert session.game_state.story_state.knowledge_status(
        "m8_fact_ashen_regent"
    ) is KnowledgeStatus.CONFIRMED


def test_archive_memory_is_unavailable_when_azhviell_is_not_active():
    game = _floor_four_midpoint_game(("branoc", "zhaivra"))
    session = _session(game)

    view = session.current_view()
    assert OverworldAction.OPEN_ARCHIVE_MEMORY not in {
        option.action for option in view.options
    }
    session.submit(ChooseOverworldAction(OverworldAction.OPEN_ARCHIVE_MEMORY))
    assert "m8_azh_archive_memory" not in session.game_state.story_state.completed_events
    assert session.game_state.story_state.knowledge_status(
        "m8_fact_ashen_regent"
    ) is KnowledgeStatus.UNKNOWN


def test_reliquary_echo_requires_claimed_story_report_and_is_non_pair_specific():
    game = completed_hub_game()
    session = _session(game)
    assert OverworldAction.OPEN_RELIQUARY_ECHO not in {
        option.action for option in session.current_view().options
    }

    game.story_state.complete_event("m8_story_reliquary_echo")
    session = _session(game)
    hub_view = session.current_view()
    assert OverworldAction.OPEN_RELIQUARY_ECHO in {
        option.action for option in hub_view.options
    }

    echo_view = session.submit(
        ChooseOverworldAction(OverworldAction.OPEN_RELIQUARY_ECHO)
    )
    assert echo_view.screen is OverworldScreen.STORY_SCENE
    assert "two expedition members" in echo_view.adventure_text.lower()
    assert "i heard" not in echo_view.adventure_text.lower()
    assert "i saw" not in echo_view.adventure_text.lower()

    response = session.submit(
        ChooseOverworldAction(OverworldAction.STORY_CONTINUE)
    )
    assert response.screen is OverworldScreen.STORY_SCENE
    completed = session.submit(ChooseOverworldAction(OverworldAction.BACK))
    assert completed.screen is OverworldScreen.HUB
    assert "m8_reliquary_echo_scene" in session.game_state.story_state.completed_events
    assert OverworldAction.OPEN_RELIQUARY_ECHO not in {
        option.action for option in completed.options
    }

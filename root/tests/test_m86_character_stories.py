from copy import deepcopy

import pytest

from app.combat.battle import Battle
from app.content.catalog import create_enemy_state, get_drifter_spec, get_route_spec
from app.content.m8_story_scenes import M8_STORY_SCENES, get_story_scene
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
from tests.persistence_test_support import remove_floor_five_approach_run_state
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

    branoc_azhvielle = scenes["m8_pair_scene_branoc_azhvielle"]
    assert "I make it mine" in " ".join(branoc_azhvielle.dialogue)
    assert [choice.label for choice in branoc_azhvielle.choices] == [
        "Read only the warning",
        "Leave the record closed",
    ]

    branoc_joruun = scenes["m8_pair_scene_branoc_joruun"]
    assert "I surrendered my rank" in " ".join(branoc_joruun.dialogue)
    assert "an irritating question" in " ".join(branoc_joruun.dialogue)
    assert [choice.label for choice in branoc_joruun.choices] == [
        "Hear Joruun speak about returning",
        "Hear Branoc speak about his choice",
    ]

    branoc_zhaivra = scenes["m8_pair_scene_branoc_zhaivra"]
    assert "I’m trying to learn the difference" in " ".join(
        branoc_zhaivra.dialogue
    )
    assert not branoc_zhaivra.choices

    archive_text = " ".join(scenes["m8_azh_archive_memory"].dialogue).lower()
    assert "ashen regent" in archive_text
    assert "archivist" in archive_text
    assert "name appeared in a record" in archive_text
    assert "whether i made that choice" in archive_text
    assert "removed the name" not in archive_text
    assert [choice.label for choice in scenes["m8_azh_archive_memory"].choices] == [
        "Ask what she remembers about the name",
        "Ask what the party should do now",
    ]

    azh_zhaivra = scenes["m8_pair_scene_azhvielle_zhaivra"]
    azh_zhaivra_text = " ".join(
        list(azh_zhaivra.dialogue)
        + [choice.response for choice in azh_zhaivra.choices]
    ).lower()
    assert "nhal voryss" in azh_zhaivra_text
    assert "first turning" in azh_zhaivra_text
    assert "lost" not in azh_zhaivra_text

    faith_text = " ".join(
        scenes["m8_pair_scene_azhvielle_joruun"].dialogue
    ).lower()
    assert "i cannot invoke holy magic" in faith_text
    assert "i still pray" in faith_text
    assert len(scenes["m8_pair_scene_azhvielle_joruun"].choices) == 2

    assert len(azh_zhaivra.choices) == 2

    joruun_zhaivra = scenes["m8_pair_scene_joruun_zhaivra"]
    assert "I’m already proud of us" in (
        " ".join(joruun_zhaivra.dialogue)
        + joruun_zhaivra.completion_response
    )
    assert not joruun_zhaivra.choices

    echo_text = " ".join(
        scenes["m8_reliquary_echo_scene"].dialogue
    ).lower()
    assert "two expedition members" in echo_text
    assert "does not identify which pair" in echo_text
    assert "my answer to the report" in echo_text
    assert "if i had been there" not in echo_text
    assert "i turned toward" not in echo_text
    assert "i wanted to go back" not in echo_text
    assert "none of them was one" not in echo_text
    assert not scenes["m8_reliquary_echo_scene"].choices


def test_existing_story_state_round_trips_through_schema_28_without_new_migration():
    game = completed_hub_game()
    game.story_state.complete_event("m8_drowned_reliquary_briefing")
    game.story_state.record_decision("legacy_story_choice", "share_warning")
    historical = build_save_document(game)
    historical["schema_version"] = 28
    remove_floor_five_approach_run_state(historical)
    original = deepcopy(historical)

    assert validate_profile_payload(historical) == original
    migrated = validate_save_document(historical)
    restored = reconstruct_game_state(historical)

    assert historical == original
    assert migrated["schema_version"] == 30
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


PAIR_STORY_COMPLETIONS = tuple(
    (pair, scene_id, index, choice.choice_id)
    for pair, scene_id in PAIR_SCENES
    for index, choice in enumerate(get_story_scene(scene_id).choices)
) + tuple(
    (pair, scene_id, None, None)
    for pair, scene_id in PAIR_SCENES
    if not get_story_scene(scene_id).choices
)


@pytest.mark.parametrize(
    ("pair", "scene_id", "choice_index", "choice_id"),
    PAIR_STORY_COMPLETIONS,
)
def test_every_pair_scene_choice_completes_and_persists_exactly_once(
    pair,
    scene_id,
    choice_index,
    choice_id,
):
    port = RecordingSavePort()
    session = _session(_floor_four_midpoint_game(pair), port)
    session.submit(ChooseOverworldAction(OverworldAction.OPEN_PAIR_STORY))

    action = (
        OverworldAction.STORY_CONTINUE
        if choice_index is None
        else (
            OverworldAction.STORY_CHOICE_ONE
            if choice_index == 0
            else OverworldAction.STORY_CHOICE_TWO
        )
    )
    response = session.submit(ChooseOverworldAction(action))

    decision_key = f"m8_story_choice_{scene_id}"
    assert response.screen is OverworldScreen.STORY_SCENE
    assert scene_id in session.game_state.story_state.completed_events
    assert session.game_state.story_state.completed_events.count(scene_id) == 1
    if choice_id is None:
        assert decision_key not in session.game_state.story_state.player_decisions
    else:
        assert session.game_state.story_state.player_decisions[decision_key] == choice_id
    assert port.save_calls == 1

    session.submit(ChooseOverworldAction(OverworldAction.BACK))
    restored = reconstruct_game_state(build_save_document(session.game_state))
    assert restored.story_state.completed_events.count(scene_id) == 1
    if choice_id is not None:
        assert restored.story_state.player_decisions[decision_key] == choice_id


@pytest.mark.parametrize(
    ("pair", "scene_id", "choice_id"),
    tuple(
        (pair, scene_id, choice.choice_id)
        for pair, scene_id in PAIR_SCENES
        for choice in get_story_scene(scene_id).choices
    ),
)
def test_pair_scene_failed_save_rolls_back_completion_and_choice_evidence(
    pair,
    scene_id,
    choice_id,
):
    port = RecordingSavePort(fail=True)
    session = _session(_floor_four_midpoint_game(pair), port)
    before = session.game_state.snapshot()
    session.submit(ChooseOverworldAction(OverworldAction.OPEN_PAIR_STORY))
    action = (
        OverworldAction.STORY_CHOICE_ONE
        if get_story_scene(scene_id).choices[0].choice_id == choice_id
        else OverworldAction.STORY_CHOICE_TWO
    )

    failed = session.submit(ChooseOverworldAction(action))

    assert failed.screen is OverworldScreen.STORY_SCENE
    assert session.game_state.snapshot() == before
    assert scene_id not in session.game_state.story_state.completed_events
    assert f"m8_story_choice_{scene_id}" not in (
        session.game_state.story_state.player_decisions
    )

    port.fail = False
    session.submit(ChooseOverworldAction(action))
    assert scene_id in session.game_state.story_state.completed_events
    assert session.game_state.story_state.player_decisions[
        f"m8_story_choice_{scene_id}"
    ] == choice_id


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
    choice_action = OverworldAction.STORY_CHOICE_ONE
    failed = session.submit(ChooseOverworldAction(choice_action))

    assert failed.screen is OverworldScreen.STORY_SCENE
    assert session.game_state.snapshot() == before
    assert "m8_azh_archive_memory" not in session.game_state.story_state.completed_events
    assert session.game_state.story_state.knowledge_status(
        "m8_fact_ashen_regent"
    ) is KnowledgeStatus.UNKNOWN
    assert "m8_story_choice_m8_azh_archive_memory" not in (
        session.game_state.story_state.player_decisions
    )

    port.fail = False
    session.submit(ChooseOverworldAction(choice_action))
    assert session.game_state.story_state.completed_events.count(
        "m8_azh_archive_memory"
    ) == 1
    assert session.game_state.story_state.knowledge_status(
        "m8_fact_ashen_regent"
    ) is KnowledgeStatus.CONFIRMED


def test_archive_memory_cancel_does_not_promote_knowledge_or_record_a_choice():
    game = _floor_four_midpoint_game(("azhvielle", "joruun"))
    session = _session(game)
    before = game.snapshot()
    session.submit(ChooseOverworldAction(OverworldAction.OPEN_ARCHIVE_MEMORY))

    cancelled = session.submit(ChooseOverworldAction(OverworldAction.CANCEL))

    assert cancelled.screen is OverworldScreen.REST
    assert session.game_state.snapshot() == before
    assert "m8_azh_archive_memory" not in game.story_state.completed_events
    assert "m8_story_choice_m8_azh_archive_memory" not in (
        game.story_state.player_decisions
    )
    assert game.story_state.knowledge_status(
        "m8_fact_ashen_regent"
    ) is KnowledgeStatus.UNKNOWN


@pytest.mark.parametrize(
    ("choice_action", "choice_id"),
    (
        (OverworldAction.STORY_CHOICE_ONE, "ask_about_missing_name"),
        (OverworldAction.STORY_CHOICE_TWO, "ask_party_plan"),
    ),
)
def test_archive_memory_choice_and_fact_survive_reload_without_duplicate(
    choice_action,
    choice_id,
):
    port = RecordingSavePort()
    session = _session(
        _floor_four_midpoint_game(("azhvielle", "joruun")),
        port,
    )
    session.submit(ChooseOverworldAction(OverworldAction.OPEN_ARCHIVE_MEMORY))
    session.submit(ChooseOverworldAction(choice_action))
    session.submit(ChooseOverworldAction(OverworldAction.BACK))

    restored = reconstruct_game_state(build_save_document(session.game_state))
    assert restored.story_state.completed_events.count(
        "m8_azh_archive_memory"
    ) == 1
    assert restored.story_state.player_decisions[
        "m8_story_choice_m8_azh_archive_memory"
    ] == choice_id
    assert restored.story_state.knowledge_status(
        "m8_fact_ashen_regent"
    ) is KnowledgeStatus.CONFIRMED

    reloaded_session = _session(restored, RecordingSavePort())
    assert OverworldAction.OPEN_ARCHIVE_MEMORY not in {
        option.action for option in reloaded_session.current_view().options
    }
    before_duplicate = restored.snapshot()
    reloaded_session.submit(
        ChooseOverworldAction(OverworldAction.OPEN_ARCHIVE_MEMORY)
    )
    assert restored.snapshot() == before_duplicate


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

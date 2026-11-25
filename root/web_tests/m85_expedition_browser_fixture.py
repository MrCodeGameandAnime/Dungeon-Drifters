"""Emit a Hub save with the six authored Floor-IV report outcomes."""

import json
from pathlib import Path
import sys
from uuid import UUID

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from app.content.catalog import get_armor_reward_source, get_drifter_spec
from app.game.armor_generation import ArmorGenerationService
from app.game.expedition_state import ExpeditionState, report_content_id_for
from app.persistence.envelope import build_profile_envelope, serialize_profile_envelope
from app.persistence.save_document import build_save_document
from app.player.player_state import PlayerState
from game_test_support import completed_hub_game


_PROFILE_ID = UUID("d4d4d4d4-0000-4000-8000-000000000001")
_CLIENT_SAVE_ID = UUID("e9000000-0000-4000-8000-000000000001")
_STARTED_AT = "2026-11-20T12:00:00Z"
_COMPLETED_AT = "2026-11-20T12:20:00Z"


class _LowestRolls:
    @staticmethod
    def randint(start, _end):
        return start


def _floor_four_armor():
    source = get_armor_reward_source("m8_floor_four_armor_source")
    return ArmorGenerationService(rng=_LowestRolls()).generate(
        template_id=source.template_id,
        floor=source.floor,
        source_id=source.source_id,
        instance_id=str(UUID("e9000000-0000-4000-8000-000000000099")),
        secured=True,
    )


def _game():
    game = completed_hub_game()
    recruited = {
        member.character.profile.drifter_id for member in game.recruited_members
    }
    for drifter_id in ("azhvielle", "branoc", "joruun", "zhaivra"):
        if drifter_id not in recruited:
            assert game.party_state.recruit_companion(
                game.player_state,
                PlayerState(get_drifter_spec(drifter_id).create_character()),
                cost=0,
            )
    game.party_state._floor_one_cleared = True
    game.party_state._floor_two_cleared = True
    game.party_state._floor_three_cleared = True
    game.party_state._floor_four_cleared = True
    game.story_state.reveal_knowledge_fact(
        "m8_fact_drowned_reliquary",
        "confirmed",
    )

    armor = _floor_four_armor().snapshot()
    outcomes = (
        (
            "material",
            {
                "source_id": "m8_floor_four_metal_drop_01",
                "reward_item_id": "grade_iv_metal",
                "reward_quantity": 1,
            },
        ),
        (
            "equipment",
            {
                "source_id": "m8_floor_four_armor_source",
                "equipment_instance": armor,
            },
        ),
        (
            "recovery",
            {
                "source_id": "m8_floor_four_recovery_source",
                "reward_item_id": "healing_potion",
                "reward_quantity": 1,
            },
        ),
        (
            "scouting",
            {
                "knowledge_fact_ids": [
                    "m8_fact_reliquary_threats",
                    "m8_fact_ashen_vault",
                    "m8_fact_ashen_regent",
                ],
            },
        ),
        ("story", {"story_event_id": "m8_story_reliquary_echo"}),
        (
            "elite",
            {
                "source_id": "m8_floor_four_core_drop_01",
                "reward_item_id": "grade_iv_cores",
                "reward_quantity": 1,
            },
        ),
    )
    expedition = ExpeditionState()
    for index, (category, outcome) in enumerate(outcomes, start=1):
        report_id = str(UUID(f"e9000000-0000-4000-8000-{index:012d}"))
        assignment = {
            "assignment_id": report_id,
            "outing_floor_id": "floor_four",
            "destination_floor_id": "floor_four",
            "category": category,
            "report_content_id": report_content_id_for("floor_four", category),
            "frozen_outcome": outcome,
            "expedition_drifter_ids": ["joruun", "zhaivra"],
            "started_at_utc": _STARTED_AT,
            "last_observed_at_utc": _COMPLETED_AT,
            "completed_at_utc": _COMPLETED_AT,
        }
        reward_item_id = outcome.get("reward_item_id")
        report = {
            "report_id": report_id,
            "outing_floor_id": assignment["outing_floor_id"],
            "destination_floor_id": assignment["destination_floor_id"],
            "category": category,
            "report_content_id": assignment["report_content_id"],
            "frozen_outcome": outcome,
            "expedition_drifter_ids": list(assignment["expedition_drifter_ids"]),
            "started_at_utc": _STARTED_AT,
            "completed_at_utc": _COMPLETED_AT,
            "secured_base_xp": 0,
            "experience_awards": {},
            "reward_item_id": reward_item_id,
            "reward_quantity": outcome.get("reward_quantity", 0),
            "claimed": False,
        }
        expedition.install_assignment(assignment)
        expedition.settle_assignment(report)
    game._expedition_state = expedition
    return game


def main():
    envelope = build_profile_envelope(
        build_save_document(_game()),
        profile_id=_PROFILE_ID,
        client_save_id=_CLIENT_SAVE_ID,
    )
    sys.stdout.write(json.dumps({
        "profile_key": f"dungeon-drifters.profile.v1.{_PROFILE_ID}",
        "envelope": serialize_profile_envelope(envelope).decode("utf-8"),
    }))


if __name__ == "__main__":
    main()

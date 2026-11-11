"""Qualified Hub profile for the passive expedition browser journey."""

import json
from pathlib import Path
import sys
from uuid import UUID

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from app.content.catalog import get_drifter_spec
from app.game.expeditions import ExpeditionState
from app.persistence.envelope import build_profile_envelope, serialize_profile_envelope
from app.persistence.save_document import build_save_document
from app.player.player_state import PlayerState
from game_test_support import completed_hub_game


def _game():
    game = completed_hub_game(gold=125)
    for drifter_id in ("joruun", "zhaivra"):
        if not game.party_state.recruit_companion(
            game.player_state,
            PlayerState(get_drifter_spec(drifter_id).create_character()),
            cost=0,
        ):
            raise AssertionError(f"could not recruit {drifter_id} for M6 fixture")
    game.party_state._floor_one_cleared = True
    game.party_state._floor_two_cleared = True
    game.party_state._floor_three_cleared = True
    roster = tuple(member.drifter_id for member in game.recruited_members)
    game.party_state.select_active_pair(
        ("branoc", "azhvielle"),
        recruited_ids=roster,
    )

    start = "2026-11-10T12:00:00Z"
    complete = "2026-11-10T12:20:00Z"
    report_id = "00000000-0000-4000-8000-000000000666"
    expedition = ExpeditionState()
    expedition.install_assignment({
        "assignment_id": report_id,
        "outing_floor_id": "floor_one",
        "destination_floor_id": "floor_two",
        "category": "material",
        "expedition_drifter_ids": ["joruun", "zhaivra"],
        "started_at_utc": start,
        "last_observed_at_utc": complete,
        "completed_at_utc": complete,
    })
    expedition.settle_assignment({
        "report_id": report_id,
        "outing_floor_id": "floor_one",
        "destination_floor_id": "floor_two",
        "category": "material",
        "expedition_drifter_ids": ["joruun", "zhaivra"],
        "started_at_utc": start,
        "completed_at_utc": complete,
        "secured_base_xp": 0,
        "experience_awards": {},
        "reward_item_id": "grade_ii_metal",
        "reward_quantity": 1,
        "claimed": False,
    })
    game._expedition_state = expedition
    return game


def main():
    envelope = serialize_profile_envelope(
        build_profile_envelope(
            build_save_document(_game()),
            profile_id=UUID("d4d4d4d4-0000-4000-8000-000000000001"),
            client_save_id=UUID("e6000000-0000-4000-8000-000000000001"),
        )
    ).decode("utf-8")
    sys.stdout.write(json.dumps({"hub": envelope}))


if __name__ == "__main__":
    main()

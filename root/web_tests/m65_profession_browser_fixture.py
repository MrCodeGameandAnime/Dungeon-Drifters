"""Controlled Hub profile for M6.5 profession browser journeys."""

import json
from pathlib import Path
import sys
from uuid import UUID


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from app.items.equipment import EquipmentInstance
from app.persistence.envelope import build_profile_envelope, serialize_profile_envelope
from app.persistence.save_document import build_save_document
from game_test_support import completed_hub_game


def _game():
    game = completed_hub_game(gold=250)
    party = game.party_state
    party.add_equipment_instance(
        EquipmentInstance.create(
            instance_id="e6500000-0000-4000-8000-000000000101",
            definition_id="field_chest",
            source_id="m65_browser_enchanting_chest",
            secured=True,
            stat_bonuses={"constitution": 2},
            rarity="uncommon",
        )
    )
    party.hub_economy_state.learn_affix("bastion_grade_i")
    party.add_shared_items({"grade_i_magic_crystal": 2})
    game.member_for_drifter_id("azhvielle").mana_resource.current = 0
    return game


def main():
    envelope = serialize_profile_envelope(
        build_profile_envelope(
            build_save_document(_game()),
            profile_id=UUID("d4d4d4d4-0000-4000-8000-000000000001"),
            client_save_id=UUID("e6500000-0000-4000-8000-000000000001"),
        )
    ).decode("utf-8")
    sys.stdout.write(json.dumps({"hub": envelope}))


if __name__ == "__main__":
    main()

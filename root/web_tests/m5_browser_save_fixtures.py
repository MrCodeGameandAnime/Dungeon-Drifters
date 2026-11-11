"""Valid Hub and safe-return profiles for the M5 browser journey."""

import json
from pathlib import Path
import sys
from types import SimpleNamespace
from uuid import UUID


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from app.content.catalog import get_route_node_spec, get_route_spec
from app.game.armor_generation import ArmorGenerationService
from app.game.game_state import GameState
from app.game.run_events import RunEventService
from app.items.armor_modifier import ArmorModifierInstance
from app.items.equipment import EquipmentInstance
from app.persistence.envelope import build_profile_envelope, serialize_profile_envelope
from app.persistence.save_port_contract import SaveLoadStatus
from app.persistence.save_document import build_save_document
from game_test_support import completed_hub_game


class FixtureRng:
    def __init__(self, rolls):
        self.rolls = list(rolls)

    def randrange(self, stop):
        value = self.rolls.pop(0)
        if not 0 <= value < stop:
            raise AssertionError(f"fixture roll {value} is outside 0..{stop - 1}")
        return value

    def randint(self, minimum, maximum):
        return minimum + self.randrange(maximum - minimum + 1)


class FixtureSavePort:
    def inspect(self):
        return SimpleNamespace(status=SaveLoadStatus.MISSING)

    def load(self):
        return SimpleNamespace(status=SaveLoadStatus.MISSING)

    def save(self, _game_state):
        return SimpleNamespace(status=SaveLoadStatus.SAVED)


def _generated_helm(*, secured):
    return ArmorGenerationService(rng=FixtureRng([0, 1, 0, 0])).generate(
        template_id="field_helm",
        floor=2,
        source_id="floor_two_browser_battle_01_armor_01",
        instance_id="e5000000-0000-4000-8000-000000000101",
        secured=secured,
    )


def _equipment(
    instance_id,
    definition_id,
    source_id,
    stat_bonuses,
    *,
    rarity="common",
    modifier_slots=None,
):
    return EquipmentInstance.create(
        instance_id=instance_id,
        definition_id=definition_id,
        source_id=source_id,
        secured=True,
        stat_bonuses=stat_bonuses,
        rarity=rarity,
        modifier_slots=modifier_slots,
    )


def _hub_game():
    game = completed_hub_game(gold=200)
    party = game.party_state
    party.add_shared_items(
        {
            "grade_i_metal": 2,
            "grade_i_cores": 5,
            "grade_ii_cores": 1,
        }
    )
    party.add_equipment_instance(_generated_helm(secured=True))
    party.add_equipment_instance(
        _equipment(
            "e5000000-0000-4000-8000-000000000102",
            "field_chest",
            "m5_browser_chest",
            {"constitution": 2, "spirit": 1},
            rarity="uncommon",
            modifier_slots={"II": "ward_grade_ii"},
        )
    )
    party.add_equipment_instance(
        _equipment(
            "e5000000-0000-4000-8000-000000000103",
            "field_gloves",
            "m5_browser_sale",
            {"strength": 2},
            modifier_slots={"I": "vanguard_grade_i"},
        )
    )
    party.add_equipment_instance(
        _equipment(
            "e5000000-0000-4000-8000-000000000104",
            "field_boots",
            "m5_browser_dismantle",
            {"dexterity": 2},
            modifier_slots={"I": "bastion_grade_i"},
        )
    )
    party.add_equipment_instance(
        _equipment(
            "e5000000-0000-4000-8000-000000000105",
            "iron_ring",
            "m5_browser_static_ring",
            {"intuition": 1},
            rarity=None,
        )
    )
    party.add_equipment_instance(
        _equipment(
            "e5000000-0000-4000-8000-000000000106",
            "wayfinder_pendant",
            "m5_browser_static_pendant",
            {"spirit": 1},
            rarity=None,
        )
    )
    party.add_modifier_instance(
        ArmorModifierInstance.create(
            instance_id="e5000000-0000-4000-8000-000000000201",
            definition_id="vanguard_grade_i",
            source_id="m5_browser_replacement_modifier",
            secured=True,
        )
    )
    return game


def _outing_game():
    game = completed_hub_game()
    party = game.party_state
    if not party.start_floor_one_run():
        raise AssertionError("could not begin Floor I fixture setup")
    if not party.complete_floor_one_boss(game.active_party_members):
        raise AssertionError("could not clear Floor I fixture setup")
    if not party.start_floor_two_run(run_id_factory=lambda: "m5-browser-return-run"):
        raise AssertionError("could not begin Floor II fixture setup")
    game.overworld_state.begin_route("floor_two")
    route = get_route_spec("floor_two")
    for node in route.nodes[1:11]:
        current = get_route_node_spec(game.overworld_state.current_route_node_id)
        if current.kind.value == "rest":
            game.overworld_state.record_resolved_rest_node(current.node_id)
        game.overworld_state.advance_to(node.node_id)
    result = RunEventService(
        save_port=FixtureSavePort(),
        rng=FixtureRng([0, 1, 0, 0]),
    ).resolve_armor_reward(
        game,
        node_id="floor_two_battle_09",
        template_id="field_helm",
        source_id="floor_two_browser_return_armor_01",
        instance_id_factory=lambda: "e5000000-0000-4000-8000-000000000301",
    )
    if result.status.value != "resolved":
        raise AssertionError("could not persist the unsecured armor reward fixture")
    return result.game_state


def _envelope(game, profile_id, save_id):
    return serialize_profile_envelope(
        build_profile_envelope(
            build_save_document(game),
            profile_id=UUID(profile_id),
            client_save_id=UUID(save_id),
        )
    ).decode("utf-8")


def main():
    result = {
        "hub": _envelope(
            _hub_game(),
            "d4d4d4d4-0000-4000-8000-000000000001",
            "e5000000-0000-4000-8000-000000000002",
        ),
        "outing": _envelope(
            _outing_game(),
            "d4d4d4d4-0000-4000-8000-000000000001",
            "e5000000-0000-4000-8000-000000000004",
        ),
    }
    sys.stdout.write(json.dumps(result))


if __name__ == "__main__":
    main()

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.player.character import BlackMage, Brawler, Monk, Move, RogueArcher


PLAYABLE_CLASSES = [
    Brawler,
    BlackMage,
    RogueArcher,
    Monk,
]


def test_all_playable_classes_have_structured_moves():
    for class_type in PLAYABLE_CLASSES:
        player = class_type()

        assert player.combat_moves
        assert len(player.combat_moves) == len(player.moves)

        for move in player.combat_moves:
            assert isinstance(move, Move)
            assert move.name in player.moves.values()
            assert move.mana_cost >= 0
            assert move.power > 0
            assert move.scales_with in {
                "strength",
                "constitution",
                "intelligence",
                "dexterity",
                "charisma",
            }
            assert 1 <= move.accuracy <= 100
            assert move.target in {"enemy", "self"}
            assert move.mechanic
            assert move.description


def test_each_playable_class_has_a_distinct_mechanic():
    mechanics = {class_type().class_mechanic["name"] for class_type in PLAYABLE_CLASSES}

    assert mechanics == {
        "Momentum",
        "Arcane Focus",
        "Precision",
        "Ki Forms",
    }


def test_black_mage_heal_is_defined_as_healing_not_damage():
    black_mage = BlackMage()
    heal = next(move for move in black_mage.combat_moves if move.name == "heal")

    assert heal.kind == "healing"
    assert heal.target == "self"
    assert heal.scales_with == "intelligence"


def test_battle_is_not_wired_to_structured_moves_yet():
    monk = Monk()

    assert list(monk.moves.values())[:2] == [
        "Bring The Horse To Water",
        "Sweep The Leaves",
    ]
    assert monk.combat_moves[0].name == "Bring The Horse To Water"
    assert monk.combat_moves[0].mana_cost > 0


if __name__ == "__main__":
    test_all_playable_classes_have_structured_moves()
    test_each_playable_class_has_a_distinct_mechanic()
    test_black_mage_heal_is_defined_as_healing_not_damage()
    test_battle_is_not_wired_to_structured_moves_yet()
    print("Character move data test passed.")

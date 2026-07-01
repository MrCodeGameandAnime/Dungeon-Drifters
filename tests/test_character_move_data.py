from app.combat.move import DamageType, Move, MoveKind, ResourceType, ScalingAttribute, TargetType
from app.player.character import BlackMage, Brawler, Monk, RogueArcher


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
            assert move.kind in {MoveKind.DAMAGE, MoveKind.HEALING, MoveKind.UTILITY}
            assert move.resource_type in {
                ResourceType.NONE,
                ResourceType.MANA,
                ResourceType.SUPER,
            }
            assert move.resource_cost >= 0
            assert move.power >= 0
            assert move.scales_with
            assert all(isinstance(attribute, ScalingAttribute) for attribute in move.scales_with)
            assert 0 <= move.accuracy <= 100
            assert move.target in {TargetType.ENEMY, TargetType.SELF}
            assert move.damage_type in {
                DamageType.NONE,
                DamageType.PHYSICAL,
                DamageType.MAGICAL,
                DamageType.HYBRID,
                DamageType.HEALING,
            }
            assert move.mechanic is None or move.mechanic
            assert move.description


def test_each_playable_class_has_a_distinct_mechanic():
    mechanics = {class_type().class_mechanic["name"] for class_type in PLAYABLE_CLASSES}

    assert mechanics == {
        "Heavy Vanguard",
        "Arcane Focus",
        "Precision",
        "Ki Forms",
    }


def test_black_mage_heal_is_defined_as_healing_not_damage():
    black_mage = BlackMage()
    heal = next(move for move in black_mage.combat_moves if move.name == "heal")

    assert heal.kind == MoveKind.HEALING
    assert heal.target == TargetType.SELF
    assert heal.scales_with == (ScalingAttribute.INTELLIGENCE,)
    assert heal.resource_type == ResourceType.MANA
    assert heal.damage_type == DamageType.HEALING


def test_loadout_resource_types_follow_authored_class_resources():
    brawler = Brawler()
    black_mage = BlackMage()
    rogue_archer = RogueArcher()
    monk = Monk()

    assert [move.resource_type for move in brawler.combat_moves] == [
        ResourceType.NONE,
        ResourceType.MANA,
        ResourceType.MANA,
    ]
    assert {move.resource_type for move in black_mage.combat_moves} == {ResourceType.MANA}
    assert {move.resource_type for move in rogue_archer.combat_moves} == {ResourceType.NONE}
    assert {move.resource_cost for move in rogue_archer.combat_moves} == {0}
    assert [move.resource_type for move in monk.combat_moves] == [
        ResourceType.NONE,
        ResourceType.MANA,
        ResourceType.MANA,
        ResourceType.MANA,
        ResourceType.SUPER,
    ]
    assert monk.combat_moves[0].resource_cost == 0
    assert monk.combat_moves[-1].name == "Coagulated Torrent"
    assert monk.combat_moves[-1].resource_cost == 100


def test_battle_is_not_wired_to_structured_moves_yet():
    monk = Monk()

    assert list(monk.moves.values())[:2] == [
        "Bring the Horse to Water",
        "Lightning Palm",
    ]
    assert monk.combat_moves[0].name == "Bring the Horse to Water"
    assert monk.combat_moves[0].resource_type == ResourceType.NONE
    assert monk.combat_moves[-1].resource_type == ResourceType.SUPER
    assert monk.combat_moves[-1].resource_cost == 100

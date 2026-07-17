from app.combat.move import DamageType, Move, MoveKind, ResourceType, ScalingAttribute, TargetType
from app.combat.move_presentation import MoveRole
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


def test_all_playable_rosters_keep_current_super_and_mechanic_boundary():
    supported_mechanics = {
        None,
        "basic_attack",
        "heavy_attack",
        "gravemantle_rupture",
        "infused_barb",
        "hydro_whip",
        "lightning_palm",
        "tempest_surge",
    }
    authored_deferred_mechanics = {"brace"}
    deferred_mechanics = {
        "stagger",
        "burn",
        "arcane_recovery",
        "shock",
        "crit_bonus",
        "multi_hit",
        "volley",
        "staff_control",
        "lightning",
        "storm",
        "water",
        "super",
    }

    for class_type in PLAYABLE_CLASSES:
        player = class_type()
        super_moves = [
            move
            for move in player.combat_moves
            if move.resource_type == ResourceType.SUPER
        ]
        standard_moves = [
            move
            for move in player.combat_moves
            if move.resource_type != ResourceType.SUPER
        ]

        assert len(player.combat_moves) == 5
        assert len(standard_moves) == 4
        assert len(super_moves) == 1
        assert super_moves[0].resource_cost == 100
        assert all(
            move.mechanic in supported_mechanics | authored_deferred_mechanics
            for move in player.combat_moves
        )
        assert all(move.mechanic not in deferred_mechanics for move in player.combat_moves)


def test_black_mage_roster_is_four_standard_attacks_and_one_super():
    black_mage = BlackMage()

    assert [move.name for move in black_mage.combat_moves] == [
        "Scepter Sweep",
        "Gloamweight Sepulcher",
        "Mournglass Bloom",
        "Gravemantle Rupture",
        "Causality Nullwake",
    ]
    assert all(move.kind == MoveKind.DAMAGE for move in black_mage.combat_moves)
    assert [move.resource_type for move in black_mage.combat_moves] == [
        ResourceType.NONE,
        ResourceType.MANA,
        ResourceType.MANA,
        ResourceType.MANA,
        ResourceType.SUPER,
    ]
    assert black_mage.combat_moves[-1].resource_cost == 100
    assert {move.name for move in black_mage.combat_moves}.isdisjoint(
        {"fireball", "heal", "thunderbolt"}
    )
    assert all(
        move.mechanic in {None, "basic_attack", "heavy_attack", "gravemantle_rupture"}
        for move in black_mage.combat_moves
    )
    assert all(
        move.mechanic is None or move.mechanic == "gravemantle_rupture"
        for move in black_mage.combat_moves[1:]
    )
    assert all(
        move.is_spell is (move.name != "Scepter Sweep")
        for move in black_mage.combat_moves
    )


def test_brawler_roster_is_four_standard_attacks_and_one_super():
    brawler = Brawler()

    assert [move.name for move in brawler.combat_moves] == [
        "Crestgrave Reaping",
        "Cinderlung Vesper",
        "Brace",
        "Ironwake Dismemberment",
        "Third Gate Obsequy",
    ]
    assert [move.kind for move in brawler.combat_moves] == [
        MoveKind.DAMAGE,
        MoveKind.DAMAGE,
        MoveKind.UTILITY,
        MoveKind.DAMAGE,
        MoveKind.DAMAGE,
    ]
    assert [move.resource_type for move in brawler.combat_moves] == [
        ResourceType.NONE,
        ResourceType.MANA,
        ResourceType.MANA,
        ResourceType.NONE,
        ResourceType.SUPER,
    ]
    brace = brawler.combat_moves[2]
    assert brace.target == TargetType.SELF
    assert brace.resource_cost == 5
    assert brace.power == 0
    assert brace.scales_with == (ScalingAttribute.NONE,)
    assert brace.accuracy == 100
    assert brace.damage_type == DamageType.NONE
    assert brace.mechanic == "brace"
    assert brawler.combat_moves[-1].resource_cost == 100
    assert {move.name for move in brawler.combat_moves}.isdisjoint(
        {"slash", "jumping slash", "suplex"}
    )
    assert all(
        move.mechanic in {None, "basic_attack", "heavy_attack", "brace"}
        for move in brawler.combat_moves
    )
    assert [move.presentation.role for move in brawler.combat_moves] == [
        MoveRole.NORMAL,
        MoveRole.NORMAL,
        MoveRole.UTILITY,
        MoveRole.HEAVY,
        MoveRole.SUPER,
    ]
    assert brawler.combat_moves[1].presentation.affinity_label == "Fire"
    assert brawler.combat_moves[3].presentation.static_summary == (
        "A crushing Sunder-Spire strike."
    )
    assert all(move.presentation is not None for move in brawler.combat_moves)


def test_rogue_archer_roster_is_four_standard_attacks_and_one_super():
    rogue_archer = RogueArcher()

    assert [move.name for move in rogue_archer.combat_moves] == [
        "Mournpoint Verdict",
        "Hollowstring Trine",
        "Nightskein Deluge",
        "Infused Barb",
        "Starless Meridian Obsequy",
    ]
    assert all(move.kind == MoveKind.DAMAGE for move in rogue_archer.combat_moves)
    assert [move.resource_type for move in rogue_archer.combat_moves] == [
        ResourceType.NONE,
        ResourceType.MANA,
        ResourceType.MANA,
        ResourceType.MANA,
        ResourceType.SUPER,
    ]
    assert rogue_archer.combat_moves[-1].resource_cost == 100
    assert {move.name for move in rogue_archer.combat_moves}.isdisjoint(
        {"deadshot", "triple shot", "rain of arrows", "flaming arrow"}
    )
    assert all(
        move.mechanic in {
            None,
            "basic_attack",
            "heavy_attack",
            "infused_barb",
        }
        for move in rogue_archer.combat_moves
    )
    assert rogue_archer.combat_moves[0].mechanic == "basic_attack"
    assert all(move.mechanic is None for move in rogue_archer.combat_moves[1:3])
    assert rogue_archer.combat_moves[3].mechanic == "infused_barb"
    assert rogue_archer.combat_moves[4].mechanic is None


def test_loadout_resource_types_follow_authored_class_resources():
    brawler = Brawler()
    black_mage = BlackMage()
    rogue_archer = RogueArcher()
    monk = Monk()

    assert [move.resource_type for move in brawler.combat_moves] == [
        ResourceType.NONE,
        ResourceType.MANA,
        ResourceType.MANA,
        ResourceType.NONE,
        ResourceType.SUPER,
    ]
    assert [move.resource_type for move in black_mage.combat_moves] == [
        ResourceType.NONE,
        ResourceType.MANA,
        ResourceType.MANA,
        ResourceType.MANA,
        ResourceType.SUPER,
    ]
    assert [move.resource_type for move in rogue_archer.combat_moves] == [
        ResourceType.NONE,
        ResourceType.MANA,
        ResourceType.MANA,
        ResourceType.MANA,
        ResourceType.SUPER,
    ]
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

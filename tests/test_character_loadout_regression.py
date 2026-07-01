from app.items.weapon import NeedleOfPlainIron, Sathren, SkyNeedle, SunderSpire
from app.player.character import BlackMage, Brawler, Monk, RogueArcher


EXPECTED_LOADOUTS = {
    Brawler: {
        "attributes": {
            "constitution": 14,
            "spirit": 6,
            "intelligence": 5,
            "strength": 15,
            "dexterity": 10,
            "intuition": 10,
        },
        "hp": 60,
        "mana": 10,
        "name": "Brawler",
        "moves": {1: "slash", 2: "jumping slash", 3: "suplex"},
        "combat_moves": [
            {
                "name": "slash",
                "kind": "damage",
                "resource_type": "none",
                "resource_cost": 0,
                "power": 9,
                "scales_with": ["strength"],
                "accuracy": 92,
                "target": "enemy",
                "damage_type": "physical",
                "mechanic": "basic_attack",
                "description": "A reliable close-range strike.",
            },
            {
                "name": "jumping slash",
                "kind": "damage",
                "resource_type": "mana",
                "resource_cost": 3,
                "power": 14,
                "scales_with": ["strength"],
                "accuracy": 82,
                "target": "enemy",
                "damage_type": "physical",
                "mechanic": "heavy_attack",
                "description": "A risky leaping attack that hits harder than a basic strike.",
            },
            {
                "name": "suplex",
                "kind": "damage",
                "resource_type": "mana",
                "resource_cost": 5,
                "power": 18,
                "scales_with": ["strength"],
                "accuracy": 75,
                "target": "enemy",
                "damage_type": "physical",
                "mechanic": "stagger",
                "description": "A brutal throw that can stagger a weakened foe.",
            },
        ],
        "class_mechanic": {
            "name": "Heavy Vanguard",
            "description": "A durable frontline identity built around heavy physical pressure.",
        },
        "starting_weapon": SunderSpire,
    },
    BlackMage: {
        "attributes": {
            "constitution": 7,
            "spirit": 13,
            "intelligence": 15,
            "strength": 5,
            "dexterity": 8,
            "intuition": 12,
        },
        "hp": 30,
        "mana": 70,
        "name": "Black Mage",
        "moves": {1: "fireball", 2: "heal", 3: "thunderbolt"},
        "combat_moves": [
            {
                "name": "fireball",
                "kind": "damage",
                "resource_type": "mana",
                "resource_cost": 8,
                "power": 14,
                "scales_with": ["intelligence"],
                "accuracy": 88,
                "target": "enemy",
                "damage_type": "magical",
                "mechanic": "burn",
                "description": "A direct fire spell with a chance to leave burning damage later.",
            },
            {
                "name": "heal",
                "kind": "healing",
                "resource_type": "mana",
                "resource_cost": 10,
                "power": 12,
                "scales_with": ["intelligence"],
                "accuracy": 100,
                "target": "self",
                "damage_type": "healing",
                "mechanic": "arcane_recovery",
                "description": "Restores health instead of damaging the enemy.",
            },
            {
                "name": "thunderbolt",
                "kind": "damage",
                "resource_type": "mana",
                "resource_cost": 14,
                "power": 20,
                "scales_with": ["intelligence"],
                "accuracy": 78,
                "target": "enemy",
                "damage_type": "magical",
                "mechanic": "shock",
                "description": "A volatile lightning spell with high damage and lower accuracy.",
            },
        ],
        "class_mechanic": {
            "name": "Arcane Focus",
            "resource": "mana",
            "description": "Spells spend mana and scale primarily from intelligence.",
        },
        "starting_weapon": NeedleOfPlainIron,
    },
    RogueArcher: {
        "attributes": {
            "constitution": 8,
            "spirit": 7,
            "intelligence": 10,
            "strength": 6,
            "dexterity": 15,
            "intuition": 14,
        },
        "hp": 45,
        "mana": 20,
        "name": "Rogue Archer",
        "moves": {1: "deadshot", 2: "triple shot", 3: "rain of arrows", 4: "flaming arrow"},
        "combat_moves": [
            {
                "name": "deadshot",
                "kind": "damage",
                "resource_type": "none",
                "resource_cost": 0,
                "power": 12,
                "scales_with": ["dexterity"],
                "accuracy": 95,
                "target": "enemy",
                "damage_type": "physical",
                "mechanic": "crit_bonus",
                "description": "A precise shot with increased critical potential.",
            },
            {
                "name": "triple shot",
                "kind": "damage",
                "resource_type": "none",
                "resource_cost": 0,
                "power": 6,
                "scales_with": ["dexterity"],
                "accuracy": 86,
                "target": "enemy",
                "damage_type": "physical",
                "mechanic": "multi_hit",
                "description": "Fires three lighter shots that can each contribute damage.",
            },
            {
                "name": "rain of arrows",
                "kind": "damage",
                "resource_type": "none",
                "resource_cost": 0,
                "power": 10,
                "scales_with": ["dexterity"],
                "accuracy": 80,
                "target": "enemy",
                "damage_type": "physical",
                "mechanic": "volley",
                "description": "A broad volley designed for future multi-enemy encounters.",
            },
            {
                "name": "flaming arrow",
                "kind": "damage",
                "resource_type": "none",
                "resource_cost": 0,
                "power": 13,
                "scales_with": ["dexterity", "intuition"],
                "accuracy": 84,
                "target": "enemy",
                "damage_type": "hybrid",
                "mechanic": "burn",
                "description": "A dexterous shot with a fire effect hook for later status damage.",
            },
        ],
        "class_mechanic": {
            "name": "Precision",
            "description": "High dexterity supports accuracy, critical hits, and multi-hit attacks.",
        },
        "starting_weapon": Sathren,
    },
    Monk: {
        "attributes": {
            "constitution": 10,
            "spirit": 10,
            "intelligence": 13,
            "strength": 7,
            "dexterity": 12,
            "intuition": 8,
        },
        "hp": 60,
        "mana": 20,
        "name": "Monk",
        "moves": {
            1: "Bring the Horse to Water",
            2: "Lightning Palm",
            3: "Tempest Surge",
            4: "Hydro Whip",
            5: "Coagulated Torrent",
        },
        "combat_moves": [
            {
                "name": "Bring the Horse to Water",
                "kind": "damage",
                "resource_type": "none",
                "resource_cost": 0,
                "power": 12,
                "scales_with": ["dexterity"],
                "accuracy": 90,
                "target": "enemy",
                "damage_type": "physical",
                "mechanic": "staff_control",
                "description": "A grounded staff technique that redirects force through precise positioning.",
            },
            {
                "name": "Lightning Palm",
                "kind": "damage",
                "resource_type": "mana",
                "resource_cost": 6,
                "power": 16,
                "scales_with": ["dexterity", "intelligence", "intuition"],
                "accuracy": 70,
                "target": "enemy",
                "damage_type": "hybrid",
                "mechanic": "lightning",
                "description": "A risky palm strike that carries lightning through the point of impact.",
            },
            {
                "name": "Tempest Surge",
                "kind": "damage",
                "resource_type": "mana",
                "resource_cost": 6,
                "power": 12,
                "scales_with": ["intelligence", "intuition"],
                "accuracy": 80,
                "target": "enemy",
                "damage_type": "magical",
                "mechanic": "storm",
                "description": "A controlled burst of storm force shaped through Sky-Needle.",
            },
            {
                "name": "Hydro Whip",
                "kind": "damage",
                "resource_type": "mana",
                "resource_cost": 4,
                "power": 8,
                "scales_with": ["intelligence", "intuition"],
                "accuracy": 80,
                "target": "enemy",
                "damage_type": "magical",
                "mechanic": "water",
                "description": "A snapping water current used to lash and reposition an enemy.",
            },
            {
                "name": "Coagulated Torrent",
                "kind": "damage",
                "resource_type": "super",
                "resource_cost": 100,
                "power": 24,
                "scales_with": ["intelligence", "intuition"],
                "accuracy": 100,
                "target": "enemy",
                "damage_type": "magical",
                "mechanic": "super",
                "description": "A decisive torrent that compresses gathered force into a finishing surge.",
            },
        ],
        "class_mechanic": {
            "name": "Ki Forms",
            "description": "Monk techniques combine positioning, balance, and Ki setup effects.",
        },
        "starting_weapon": SkyNeedle,
    },
}


def move_to_dict(move):
    return {
        "name": move.name,
        "kind": move.kind.value,
        "resource_type": move.resource_type.value,
        "resource_cost": move.resource_cost,
        "power": move.power,
        "scales_with": [
            attribute.value
            for attribute in move.scales_with
        ],
        "accuracy": move.accuracy,
        "target": move.target.value,
        "damage_type": move.damage_type.value,
        "mechanic": move.mechanic,
        "description": move.description,
    }


def test_all_archetype_authored_loadout_data_is_unchanged():
    for class_type, expected in EXPECTED_LOADOUTS.items():
        player = class_type()

        assert player.permanent_stats.as_dict() == expected["attributes"]
        assert player.permanent_stats.total == 60
        assert not hasattr(player, "charisma")
        assert player.health.maximum == expected["hp"]
        assert player.health.current == expected["hp"]
        assert player.mana_resource.maximum == expected["mana"]
        assert player.mana_resource.current == expected["mana"]
        assert player.name == expected["name"]
        assert player.moves == expected["moves"]
        assert [move.name for move in player.combat_moves] == [
            move["name"] for move in expected["combat_moves"]
        ]
        assert [move_to_dict(move) for move in player.combat_moves] == expected["combat_moves"]
        assert player.class_mechanic == expected["class_mechanic"]
        assert isinstance(player.starting_equipment["weapon"], expected["starting_weapon"])


def test_branoc_has_no_active_momentum_hooks_or_resource_declaration():
    player = Brawler()
    slash, jumping_slash, suplex = player.combat_moves
    forbidden_builder = "combo" + "_" + "builder"
    forbidden_spender = "combo" + "_" + "spender"

    assert slash.mechanic != forbidden_builder
    assert "momentum" not in slash.description.lower()
    assert jumping_slash.mechanic != forbidden_spender
    jumping_description = jumping_slash.description.lower()
    assert "momentum" not in jumping_description
    assert "spend" not in jumping_description
    assert "require" not in jumping_description
    assert "benefit" not in jumping_description
    assert suplex.mechanic == "stagger"
    assert player.class_mechanic["name"] != "Momentum"
    assert "resource" not in player.class_mechanic


def test_zhaivra_and_joruun_do_not_declare_focus_or_ki_resources():
    zhaivra = RogueArcher()
    joruun = Monk()

    assert "resource" not in zhaivra.class_mechanic
    assert zhaivra.class_mechanic["name"] == "Precision"
    assert {move.resource_type.value for move in zhaivra.combat_moves} == {"none"}
    assert {move.resource_cost for move in zhaivra.combat_moves} == {0}

    assert "resource" not in joruun.class_mechanic
    assert joruun.class_mechanic["name"] == "Ki Forms"
    assert {move.resource_type.value for move in joruun.combat_moves} == {
        "none",
        "mana",
        "super",
    }

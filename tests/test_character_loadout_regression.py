import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

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
                "kind": "physical_damage",
                "mana_cost": 0,
                "power": 9,
                "scales_with": "strength",
                "accuracy": 92,
                "target": "enemy",
                "mechanic": "combo_builder",
                "description": "A reliable close-range strike that builds momentum.",
            },
            {
                "name": "jumping slash",
                "kind": "physical_damage",
                "mana_cost": 3,
                "power": 14,
                "scales_with": "strength",
                "accuracy": 82,
                "target": "enemy",
                "mechanic": "combo_spender",
                "description": "A risky leaping attack that hits harder after momentum is built.",
            },
            {
                "name": "suplex",
                "kind": "physical_damage_control",
                "mana_cost": 5,
                "power": 18,
                "scales_with": "strength",
                "accuracy": 75,
                "target": "enemy",
                "mechanic": "stagger",
                "description": "A brutal throw that can stagger a weakened foe.",
            },
        ],
        "class_mechanic": {
            "name": "Momentum",
            "resource": "momentum",
            "description": "Basic hits build momentum; heavy techniques spend it for burst damage.",
        },
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
                "kind": "magic_damage",
                "mana_cost": 8,
                "power": 14,
                "scales_with": "intelligence",
                "accuracy": 88,
                "target": "enemy",
                "mechanic": "burn",
                "description": "A direct fire spell with a chance to leave burning damage later.",
            },
            {
                "name": "heal",
                "kind": "healing",
                "mana_cost": 10,
                "power": 12,
                "scales_with": "intelligence",
                "accuracy": 100,
                "target": "self",
                "mechanic": "arcane_recovery",
                "description": "Restores health instead of damaging the enemy.",
            },
            {
                "name": "thunderbolt",
                "kind": "magic_damage",
                "mana_cost": 14,
                "power": 20,
                "scales_with": "intelligence",
                "accuracy": 78,
                "target": "enemy",
                "mechanic": "shock",
                "description": "A volatile lightning spell with high damage and lower accuracy.",
            },
        ],
        "class_mechanic": {
            "name": "Arcane Focus",
            "resource": "mana",
            "description": "Spells spend mana and scale primarily from intelligence.",
        },
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
                "kind": "precision_damage",
                "mana_cost": 4,
                "power": 12,
                "scales_with": "dexterity",
                "accuracy": 95,
                "target": "enemy",
                "mechanic": "crit_bonus",
                "description": "A precise shot with increased critical potential.",
            },
            {
                "name": "triple shot",
                "kind": "multi_hit_damage",
                "mana_cost": 6,
                "power": 6,
                "scales_with": "dexterity",
                "accuracy": 86,
                "target": "enemy",
                "mechanic": "multi_hit",
                "description": "Fires three lighter shots that can each contribute damage.",
            },
            {
                "name": "rain of arrows",
                "kind": "area_damage",
                "mana_cost": 8,
                "power": 10,
                "scales_with": "dexterity",
                "accuracy": 80,
                "target": "enemy",
                "mechanic": "volley",
                "description": "A broad volley designed for future multi-enemy encounters.",
            },
            {
                "name": "flaming arrow",
                "kind": "hybrid_damage",
                "mana_cost": 7,
                "power": 13,
                "scales_with": "dexterity",
                "accuracy": 84,
                "target": "enemy",
                "mechanic": "burn",
                "description": "A dexterous shot with a fire effect hook for later status damage.",
            },
        ],
        "class_mechanic": {
            "name": "Precision",
            "resource": "focus",
            "description": "High dexterity supports accuracy, critical hits, and multi-hit attacks.",
        },
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
            1: "Bring The Horse To Water",
            2: "Sweep The Leaves",
            3: "5-foot punch",
            4: "Waki Gamae Kamae Kata",
            5: "Carry Water",
        },
        "combat_moves": [
            {
                "name": "Bring The Horse To Water",
                "kind": "physical_damage_control",
                "mana_cost": 3,
                "power": 10,
                "scales_with": "strength",
                "accuracy": 90,
                "target": "enemy",
                "mechanic": "brace",
                "description": "Braces the staff and pulls the target into the strike.",
            },
            {
                "name": "Sweep The Leaves",
                "kind": "physical_damage_control",
                "mana_cost": 4,
                "power": 11,
                "scales_with": "dexterity",
                "accuracy": 88,
                "target": "enemy",
                "mechanic": "trip",
                "description": "A low strike that can knock the enemy off balance.",
            },
            {
                "name": "5-foot punch",
                "kind": "ki_damage",
                "mana_cost": 5,
                "power": 13,
                "scales_with": "strength",
                "accuracy": 86,
                "target": "enemy",
                "mechanic": "ki_burst",
                "description": "A focused staff thrust that channels Ki through impact.",
            },
            {
                "name": "Waki Gamae Kamae Kata",
                "kind": "charged_damage",
                "mana_cost": 8,
                "power": 20,
                "scales_with": "constitution",
                "accuracy": 76,
                "target": "enemy",
                "mechanic": "charged_counter",
                "description": "A committed overhead form best used after bracing or defending.",
            },
            {
                "name": "Carry Water",
                "kind": "finisher_damage",
                "mana_cost": 10,
                "power": 24,
                "scales_with": "strength",
                "accuracy": 72,
                "target": "enemy",
                "mechanic": "prone_finisher",
                "description": "A heavy finishing maneuver against a vulnerable or prone foe.",
            },
        ],
        "class_mechanic": {
            "name": "Ki Forms",
            "resource": "ki",
            "description": "Monk techniques combine positioning, balance, and Ki setup effects.",
        },
    },
}


def move_to_dict(move):
    return {
        "name": move.name,
        "kind": move.kind,
        "mana_cost": move.mana_cost,
        "power": move.power,
        "scales_with": move.scales_with,
        "accuracy": move.accuracy,
        "target": move.target,
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


if __name__ == "__main__":
    test_all_archetype_authored_loadout_data_is_unchanged()
    print("Character loadout regression test passed.")

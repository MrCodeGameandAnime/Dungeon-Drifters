from app.items.weapon import NeedleOfPlainIron, Sathren, SkyNeedle, SunderSpire
from app.player.character import BlackMage, Brawler, Monk, RogueArcher
from app.player.loadouts import azhvielle, branoc, joruun, zhaivra


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
        "hp": 116,
        "mana": 46,
        "name": "Brawler",
        "moves": {
            1: "Crestgrave Reaping",
            2: "Cinderlung Vesper",
            3: "Brace",
            4: "Ironwake Dismemberment",
            5: "Third Gate Obsequy",
        },
        "combat_moves": [
            {
                "name": "Crestgrave Reaping",
                "kind": "damage",
                "resource_type": "none",
                "resource_cost": 0,
                "power": 9,
                "scales_with": ["strength"],
                "accuracy": 92,
                "target": "enemy",
                "damage_type": "physical",
                "mechanic": "basic_attack",
                "description": "Sunder-Spire tears through the target, cleaving guard and armor.",
            },
            {
                "name": "Cinderlung Vesper",
                "kind": "damage",
                "resource_type": "mana",
                "resource_cost": 3,
                "power": 8,
                "scales_with": ["spirit"],
                "accuracy": 88,
                "target": "enemy",
                "damage_type": "magical",
                "mechanic": None,
                "description": "A black war-breath erupts forward, searing everything in its path.",
            },
            {
                "name": "Brace",
                "kind": "utility",
                "resource_type": "mana",
                "resource_cost": 5,
                "power": 0,
                "scales_with": ["none"],
                "accuracy": 100,
                "target": "self",
                "damage_type": "none",
                "mechanic": "brace",
                "description": "Branoc plants Sunder-Spire and braces behind the Deep-Iron crest.",
            },
            {
                "name": "Ironwake Dismemberment",
                "kind": "damage",
                "resource_type": "none",
                "resource_cost": 0,
                "power": 14,
                "scales_with": ["strength"],
                "accuracy": 82,
                "target": "enemy",
                "damage_type": "physical",
                "mechanic": "heavy_attack",
                "description": "Branoc drives Sunder-Spire downward with battlefield-splitting force.",
            },
            {
                "name": "Third Gate Obsequy",
                "kind": "damage",
                "resource_type": "super",
                "resource_cost": 100,
                "power": 24,
                "scales_with": ["strength", "spirit"],
                "accuracy": 100,
                "target": "enemy",
                "damage_type": "hybrid",
                "mechanic": None,
                "description": "A forbidden gate manifests behind Branoc, pouring ruin through Sunder-Spire.",
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
        "hp": 91,
        "mana": 56,
        "name": "Black Mage",
        "moves": {
            1: "Scepter Sweep",
            2: "Gloamweight Sepulcher",
            3: "Mournglass Bloom",
            4: "Gravemantle Rupture",
            5: "Causality Nullwake",
        },
        "combat_moves": [
            {
                "name": "Scepter Sweep",
                "kind": "damage",
                "resource_type": "none",
                "resource_cost": 0,
                "power": 7,
                "scales_with": ["dexterity"],
                "accuracy": 92,
                "target": "enemy",
                "damage_type": "physical",
                "mechanic": "basic_attack",
                "description": "A direct scepter strike aimed at the target.",
            },
            {
                "name": "Gloamweight Sepulcher",
                "kind": "damage",
                "resource_type": "mana",
                "resource_cost": 8,
                "power": 15,
                "scales_with": ["intelligence"],
                "accuracy": 86,
                "target": "enemy",
                "damage_type": "magical",
                "mechanic": None,
                "description": "Dark gravity folds inward, crushing the target beneath impossible weight.",
            },
            {
                "name": "Mournglass Bloom",
                "kind": "damage",
                "resource_type": "mana",
                "resource_cost": 6,
                "power": 12,
                "scales_with": ["intelligence", "spirit"],
                "accuracy": 90,
                "target": "enemy",
                "damage_type": "magical",
                "mechanic": None,
                "description": "Black frost erupts outward, encasing nearby enemies in splintering ice.",
            },
            {
                "name": "Gravemantle Rupture",
                "kind": "damage",
                "resource_type": "mana",
                "resource_cost": 12,
                "power": 17,
                "scales_with": ["intelligence", "spirit"],
                "accuracy": 80,
                "target": "enemy",
                "damage_type": "hybrid",
                "mechanic": "gravemantle_rupture",
                "description": "The ground ruptures beneath the target, shattering balance and armor.",
            },
            {
                "name": "Causality Nullwake",
                "kind": "damage",
                "resource_type": "super",
                "resource_cost": 100,
                "power": 30,
                "scales_with": ["intelligence", "intuition"],
                "accuracy": 100,
                "target": "enemy",
                "damage_type": "magical",
                "mechanic": None,
                "description": "Causality collapses around the target, erasing motion before it can occur.",
            },
        ],
        "class_mechanic": {
            "name": "Arcane Focus",
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
        "hp": 94,
        "mana": 47,
        "name": "Rogue Archer",
        "moves": {
            1: "Mournpoint Verdict",
            2: "Hollowstring Trine",
            3: "Nightskein Deluge",
            4: "Infused Barb",
            5: "Starless Meridian Obsequy",
        },
        "combat_moves": [
            {
                "name": "Mournpoint Verdict",
                "kind": "damage",
                "resource_type": "none",
                "resource_cost": 0,
                "power": 10,
                "scales_with": ["dexterity"],
                "accuracy": 96,
                "target": "enemy",
                "damage_type": "physical",
                "mechanic": "basic_attack",
                "description": "Zhaivra drives a single arrow through the target’s weakest point.",
            },
            {
                "name": "Hollowstring Trine",
                "kind": "damage",
                "resource_type": "mana",
                "resource_cost": 4,
                "power": 16,
                "scales_with": ["dexterity"],
                "accuracy": 86,
                "target": "enemy",
                "damage_type": "physical",
                "mechanic": None,
                "description": "Three arrows split from one release, striking in a merciless sequence.",
            },
            {
                "name": "Nightskein Deluge",
                "kind": "damage",
                "resource_type": "mana",
                "resource_cost": 6,
                "power": 15,
                "scales_with": ["dexterity", "intuition"],
                "accuracy": 82,
                "target": "enemy",
                "damage_type": "magical",
                "mechanic": None,
                "description": "A woven storm of shadow-arrows descends across the battlefield.",
            },
            {
                "name": "Infused Barb",
                "kind": "damage",
                "resource_type": "mana",
                "resource_cost": 5,
                "power": 14,
                "scales_with": ["intuition", "intelligence"],
                "accuracy": 88,
                "target": "enemy",
                "damage_type": "magical",
                "mechanic": "infused_barb",
                "description": "A prepared alchemical arrow carries fire or poison into the target.",
            },
            {
                "name": "Starless Meridian Obsequy",
                "kind": "damage",
                "resource_type": "super",
                "resource_cost": 100,
                "power": 28,
                "scales_with": ["dexterity", "intuition"],
                "accuracy": 100,
                "target": "enemy",
                "damage_type": "hybrid",
                "mechanic": None,
                "description": "Zhaivra looses an impossible shot that tears a silent path through everything before it.",
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
        "hp": 100,
        "mana": 50,
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
                "mechanic": None,
                "description": "A grounded staff technique that redirects force through precise positioning.",
            },
            {
                "name": "Lightning Palm",
                "kind": "damage",
                "resource_type": "mana",
                "resource_cost": 7,
                "power": 24,
                "scales_with": ["dexterity", "intelligence", "intuition"],
                "accuracy": 70,
                "target": "enemy",
                "damage_type": "hybrid",
                "mechanic": "lightning_palm",
                "description": "A risky palm strike that carries lightning through the point of impact.",
            },
            {
                "name": "Tempest Surge",
                "kind": "damage",
                "resource_type": "mana",
                "resource_cost": 6,
                "power": 20,
                "scales_with": ["intelligence", "intuition"],
                "accuracy": 82,
                "target": "enemy",
                "damage_type": "magical",
                "mechanic": "tempest_surge",
                "description": "A controlled burst of storm force shaped through Sky-Needle.",
            },
            {
                "name": "Hydro Whip",
                "kind": "damage",
                "resource_type": "mana",
                "resource_cost": 4,
                "power": 16,
                "scales_with": ["intelligence", "intuition"],
                "accuracy": 88,
                "target": "enemy",
                "damage_type": "magical",
                "mechanic": "hydro_whip",
                "description": "A snapping water current used to lash and reposition an enemy.",
            },
            {
                "name": "Coagulated Torrent",
                "kind": "damage",
                "resource_type": "super",
                "resource_cost": 100,
                "power": 32,
                "scales_with": ["intelligence", "intuition"],
                "accuracy": 100,
                "target": "enemy",
                "damage_type": "magical",
                "mechanic": None,
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


LOADOUT_MODULES = {
    branoc: EXPECTED_LOADOUTS[Brawler]["attributes"],
    azhvielle: EXPECTED_LOADOUTS[BlackMage]["attributes"],
    zhaivra: EXPECTED_LOADOUTS[RogueArcher]["attributes"],
    joruun: EXPECTED_LOADOUTS[Monk]["attributes"],
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


def test_authored_starting_stats_live_in_loadout_modules():
    for loadout_module, expected_stats in LOADOUT_MODULES.items():
        starting_stats = loadout_module.create_starting_stats()

        assert starting_stats == expected_stats
        assert sum(starting_stats.values()) == 60


def test_authored_starting_stats_are_returned_as_fresh_dictionaries():
    for loadout_module, expected_stats in LOADOUT_MODULES.items():
        first = loadout_module.create_starting_stats()
        second = loadout_module.create_starting_stats()

        first["constitution"] = 1

        assert second == expected_stats


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
    (
        crestgrave_reaping,
        cinderlung_vesper,
        brace,
        ironwake_dismemberment,
        third_gate_obsequy,
    ) = player.combat_moves
    forbidden_builder = "combo" + "_" + "builder"
    forbidden_spender = "combo" + "_" + "spender"

    for move in player.combat_moves:
        assert move.mechanic not in {forbidden_builder, forbidden_spender}
        assert "momentum" not in move.description.lower()

    assert crestgrave_reaping.mechanic == "basic_attack"
    assert cinderlung_vesper.mechanic is None
    assert brace.mechanic == "brace"
    assert ironwake_dismemberment.mechanic == "heavy_attack"
    assert third_gate_obsequy.mechanic is None
    assert player.class_mechanic["name"] != "Momentum"
    assert "resource" not in player.class_mechanic


def test_zhaivra_and_joruun_do_not_declare_focus_or_ki_resources():
    zhaivra = RogueArcher()
    joruun = Monk()

    assert "resource" not in zhaivra.class_mechanic
    assert zhaivra.class_mechanic["name"] == "Precision"
    assert [move.resource_type.value for move in zhaivra.combat_moves] == [
        "none",
        "mana",
        "mana",
        "mana",
        "super",
    ]
    assert zhaivra.combat_moves[-1].resource_cost == 100

    assert "resource" not in joruun.class_mechanic
    assert joruun.class_mechanic["name"] == "Ki Forms"
    assert {move.resource_type.value for move in joruun.combat_moves} == {
        "none",
        "mana",
        "super",
    }

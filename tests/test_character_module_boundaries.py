from pathlib import Path

import app.player.character as character_module
from app.combat.move import Move
from app.player.character import BlackMage, Brawler, Monk, RogueArcher
from app.player.progression import Exp, Level
from app.player.resources import Health, Mana, Super
from app.player.stats import PermanentStats, Stats

ROOT = Path(__file__).resolve().parents[1]


PLAYABLE_CLASSES = [
    Brawler,
    BlackMage,
    RogueArcher,
    Monk,
]

EXTRACTED_NAMES = {
    "Move",
    "Health",
    "Mana",
    "Super",
    "Level",
    "Exp",
    "Stats",
}


def read_source(relative_path):
    return (ROOT / "src" / relative_path).read_text(encoding="utf-8")


def test_support_classes_have_canonical_import_paths():
    assert Move.__module__ == "app.combat.move"
    assert Health.__module__ == "app.player.resources"
    assert Mana.__module__ == "app.player.resources"
    assert Super.__module__ == "app.player.resources"
    assert Level.__module__ == "app.player.progression"
    assert Exp.__module__ == "app.player.progression"
    assert Stats.__module__ == "app.player.stats"
    assert PermanentStats.__module__ == "app.player.stats"


def test_character_module_does_not_reexport_extracted_support_classes():
    for name in EXTRACTED_NAMES:
        assert name not in character_module.__dict__


def test_archetypes_use_canonical_support_objects():
    for class_type in PLAYABLE_CLASSES:
        player = class_type()

        assert isinstance(player.stats, Stats)
        assert isinstance(player.permanent_stats, PermanentStats)
        assert isinstance(player.health, Health)
        assert isinstance(player.mana_resource, Mana)
        assert isinstance(player.level_state, Level)
        assert isinstance(player.exp_state, Exp)
        assert all(isinstance(move, Move) for move in player.combat_moves)


def test_support_modules_do_not_import_character_runtime():
    assert "app.player.character" not in read_source("app/combat/move.py")
    assert "app.player.character" not in read_source("app/player/resources.py")
    assert "app.player.character" not in read_source("app/player/progression.py")
    assert "app.player.character" not in read_source("app/player/stats.py")


def test_loadouts_do_not_import_character_or_profile_modules():
    for path in [
            "app/player/loadouts/branoc.py",
            "app/player/loadouts/azhvielle.py",
            "app/player/loadouts/zhaivra.py",
            "app/player/loadouts/joruun.py"]:
        source = read_source(path)

        assert "app.player.character" not in source
        assert "app.world.character_profiles" not in source


def test_archetype_instances_do_not_share_mutable_runtime_containers():
    for class_type in PLAYABLE_CLASSES:
        first = class_type()
        second = class_type()

        assert first.moves == second.moves
        assert first.moves is not second.moves
        assert first.combat_moves == second.combat_moves
        assert first.combat_moves is not second.combat_moves
        assert first.class_mechanic == second.class_mechanic
        assert first.class_mechanic is not second.class_mechanic
        assert first.starting_equipment is not second.starting_equipment
        assert first.starting_equipment["weapon"] is not second.starting_equipment["weapon"]
        assert first.starting_equipment["weapon"].name == second.starting_equipment["weapon"].name
        assert first.permanent_stats is not second.permanent_stats
        assert first.health is not second.health
        assert first.mana_resource is not second.mana_resource
        assert first.level_state is not second.level_state
        assert first.exp_state is not second.exp_state

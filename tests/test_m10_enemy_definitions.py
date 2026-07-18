import pytest

from app.combat.battle import select_enemy_move
from app.combat.resolver import CombatResolver
from app.enemies import create_enemy_state
from app.enemies.definition import EnemyCapability, EnemyRank, EnemyRole
from app.enemies.goblin.definition import Goblin
from app.enemies.goblin_elite.definition import GoblinElite
from app.enemies.goblin_lord.definition import GoblinLord
from app.enemies.goblin_shaman.definition import GoblinShaman
from app.enemies.goblin_warrior.definition import GoblinWarrior
from app.enemies.state import EnemyState
from app.player.character import Brawler
from app.player.player_state import PlayerState


EXPECTED = {
    "goblin_warrior": {
        "definition": GoblinWarrior,
        "name": "Goblin Warrior",
        "hp": 85,
        "mana": 0,
        "stats": (4, 1, 1, 5, 2, 2),
        "rank": EnemyRank.COMMON,
        "role": EnemyRole.BRUTE,
        "capabilities": (EnemyCapability.BASIC_ATTACKS,),
        "moves": (
            ("Cleaver Strike", 0, 10, ("strength",), 92, "physical", "basic_attack"),
            ("Shieldbreaker Chop", 0, 15, ("strength",), 78, "physical", "heavy_attack"),
        ),
    },
    "goblin_shaman": {
        "definition": GoblinShaman,
        "name": "Goblin Shaman",
        "hp": 65,
        "mana": 25,
        "stats": (2, 5, 6, 1, 3, 4),
        "rank": EnemyRank.SPECIALIST,
        "role": EnemyRole.CASTER,
        "capabilities": (EnemyCapability.BASIC_ATTACKS, EnemyCapability.MAGIC),
        "moves": (
            ("Crooked Staff", 0, 7, ("dexterity",), 90, "physical", "basic_attack"),
            ("Cinder Hex", 5, 11, ("intelligence",), 90, "magical", "basic_attack"),
            ("Blight Spark", 10, 16, ("intelligence", "spirit"), 80, "magical", "heavy_attack"),
        ),
    },
    "goblin_elite": {
        "definition": GoblinElite,
        "name": "Goblin Elite",
        "hp": 130,
        "mana": 0,
        "stats": (7, 3, 2, 8, 5, 4),
        "rank": EnemyRank.ELITE,
        "role": EnemyRole.BRUTE,
        "capabilities": (EnemyCapability.BASIC_ATTACKS,),
        "moves": (
            ("Veteran Slash", 0, 13, ("strength", "dexterity"), 92, "physical", "basic_attack"),
            ("Butcher’s Advance", 0, 18, ("strength",), 84, "physical", "heavy_attack"),
            ("Executioner’s Drop", 0, 24, ("strength",), 72, "physical", "heavy_attack"),
        ),
    },
    "goblin_lord": {
        "definition": GoblinLord,
        "name": "Goblin Lord",
        "hp": 220,
        "mana": 30,
        "stats": (10, 7, 7, 11, 6, 9),
        "rank": EnemyRank.BOSS,
        "role": EnemyRole.BOSS,
        "capabilities": (EnemyCapability.BASIC_ATTACKS, EnemyCapability.MAGIC),
        "moves": (
            ("King’s Cleaver", 0, 18, ("strength",), 92, "physical", "basic_attack"),
            ("Iron Decree", 0, 25, ("strength", "intuition"), 80, "physical", "heavy_attack"),
            ("Black Banner Flame", 8, 17, ("intelligence", "spirit"), 88, "magical", "basic_attack"),
            ("Tyrant’s Ruin", 14, 26, ("strength", "intelligence"), 75, "hybrid", "heavy_attack"),
        ),
    },
}


@pytest.mark.parametrize("archetype_id, expected", EXPECTED.items())
def test_m10_enemy_definitions_match_authored_contract(archetype_id, expected):
    state = create_enemy_state(archetype_id)
    definition = state.definition

    assert isinstance(definition, expected["definition"])
    assert definition.archetype_id == archetype_id
    assert definition.name == expected["name"]
    assert (definition.hp, definition.mana) == (expected["hp"], expected["mana"])
    assert (
        definition.constitution,
        definition.spirit,
        definition.intelligence,
        definition.strength,
        definition.dexterity,
        definition.intuition,
    ) == expected["stats"]
    assert definition.rank is expected["rank"]
    assert definition.role is expected["role"]
    assert definition.behavior.value == "aggressive"
    assert definition.capabilities == frozenset(expected["capabilities"])
    assert tuple(
        (
            move.name,
            move.resource_cost,
            move.power,
            tuple(attribute.value for attribute in move.scales_with),
            move.accuracy,
            move.damage_type.value,
            move.mechanic,
        )
        for move in definition.combat_moves
    ) == expected["moves"]


DESCRIPTIONS = {
    "goblin_warrior": (
        "A disciplined cleaver strike delivered with greater force than an ordinary Goblin slash.",
        "A committed overhead chop intended to break through a defended position.",
    ),
    "goblin_shaman": (
        "A quick strike from the Shaman's crooked ritual staff.",
        "A concentrated ember of Goblin sorcery hurled at the target.",
        "The Shaman compresses unstable ritual energy into a violent magical discharge.",
    ),
    "goblin_elite": (
        "A practiced slash delivered with the speed and control of an experienced killer.",
        "The Elite surges forward and drives its weapon through the target’s guard.",
        "A brutal descending strike that sacrifices accuracy for overwhelming force.",
    ),
    "goblin_lord": (
        "The Goblin Lord swings its enormous cleaver with practiced authority.",
        "The Lord commits its full weight to a crushing blow meant to end resistance immediately.",
        "Dark fire gathers around the Lord’s battle standard before surging toward the target.",
        "The Goblin Lord combines raw physical force with unstable sorcery in one devastating assault.",
    ),
}


@pytest.mark.parametrize("archetype_id", EXPECTED)
def test_m10_enemy_descriptions_match_authored_contract(archetype_id):
    state = create_enemy_state(archetype_id)
    assert tuple(move.description for move in state.combat_moves) == DESCRIPTIONS[archetype_id]


@pytest.mark.parametrize("archetype_id", EXPECTED)
def test_m10_archetypes_support_only_tier_zero(archetype_id):
    assert create_enemy_state(archetype_id, tier=0).tier == 0
    with pytest.raises(ValueError, match="does not support tier 1"):
        create_enemy_state(archetype_id, tier=1)


def test_ordinary_goblin_values_remain_unchanged():
    state = EnemyState(Goblin())
    assert state.display_name == "Goblin"
    assert (state.health.maximum, state.mana_resource.maximum) == (60, 0)
    assert (
        state.strength,
        state.constitution,
        state.intelligence,
        state.dexterity,
        state.spirit,
        state.intuition,
    ) == (3, 2, 1, 1, 1, 1)
    assert tuple(move.name for move in state.combat_moves) == ("slash", "jumping slash")


class RecordingChoice:
    def __init__(self, selected=None):
        self.calls = []
        self.selected = selected

    def choice(self, options):
        self.calls.append(tuple(options))
        return self.selected or options[0]


@pytest.mark.parametrize("archetype_id", EXPECTED)
def test_selecting_enemy_move_does_not_mutate_mana(archetype_id):
    enemy = create_enemy_state(archetype_id)
    before = enemy.mana_resource.current
    select_enemy_move(enemy, RecordingChoice())
    assert enemy.mana_resource.current == before


def test_selection_excludes_unaffordable_shaman_mana_moves_and_keeps_staff():
    enemy = create_enemy_state("goblin_shaman")
    enemy.mana_resource.current = 4
    rng = RecordingChoice()

    selected = select_enemy_move(enemy, rng)

    assert tuple(move.name for move in rng.calls[0]) == ("Crooked Staff",)
    assert selected.name == "Crooked Staff"


@pytest.mark.parametrize("archetype_id", EXPECTED)
def test_selection_passes_each_eligible_move_once_and_each_can_be_selected(archetype_id):
    enemy = create_enemy_state(archetype_id)
    expected = tuple(enemy.combat_moves)

    for wanted in expected:
        rng = RecordingChoice(selected=wanted)
        assert select_enemy_move(enemy, rng) is wanted
        assert len(rng.calls) == 1
        assert rng.calls[0] == expected


def test_empty_legal_move_collection_fails_explicitly():
    enemy = create_enemy_state("goblin_shaman")
    enemy.mana_resource.current = 0
    enemy._combat_moves = tuple(move for move in enemy.combat_moves if move.name != "Crooked Staff")

    with pytest.raises(ValueError, match="no legal affordable moves"):
        select_enemy_move(enemy, RecordingChoice())


def test_accepted_shaman_mana_move_spends_authored_cost():
    enemy = create_enemy_state("goblin_shaman")
    target = PlayerState(Brawler())
    result = CombatResolver().resolve_move(enemy, target, "Cinder Hex")

    assert result.accepted is True
    assert result.resource_spent == 5
    assert enemy.mana_resource.current == 20


def test_accepted_crooked_staff_spends_no_mana():
    enemy = create_enemy_state("goblin_shaman")
    target = PlayerState(Brawler())
    result = CombatResolver().resolve_move(enemy, target, "Crooked Staff")

    assert result.accepted is True
    assert result.resource_spent == 0
    assert enemy.mana_resource.current == 25

from collections import Counter
from itertools import product
from types import SimpleNamespace

import pytest

from app.combat.battle import Battle
from app.content.catalog import create_drifter, create_enemy_definition
from app.enemies.state import EnemyState
from app.player.player_state import PlayerState


class AlwaysOneRng:
    def randint(self, _start, _end):
        return 1

    def choice(self, options):
        return tuple(options)[0]


def _enemy(archetype_id):
    return EnemyState(create_enemy_definition(archetype_id))


def _labels(archetype_ids):
    return Battle._build_enemy_display_labels(
        tuple(_enemy(archetype_id) for archetype_id in archetype_ids)
    )


def _counter_reference(display_names):
    counts = Counter(display_names)
    positions = Counter()
    labels = []
    for name in display_names:
        if counts[name] == 1:
            labels.append(name)
            continue
        positions[name] += 1
        labels.append(f"{name} {positions[name]}")
    return tuple(labels)


@pytest.mark.parametrize(
    ("archetype_ids", "expected"),
    (
        (("goblin",), ("Goblin",)),
        (("goblin", "goblin"), ("Goblin 1", "Goblin 2")),
        (
            ("goblin", "goblin", "goblin"),
            ("Goblin 1", "Goblin 2", "Goblin 3"),
        ),
        (
            ("goblin", "goblin_shaman"),
            ("Goblin", "Goblin Shaman"),
        ),
        (
            ("goblin", "goblin_shaman", "goblin"),
            ("Goblin 1", "Goblin Shaman", "Goblin 2"),
        ),
        (
            ("goblin", "goblin_shaman", "goblin", "goblin_shaman"),
            (
                "Goblin 1",
                "Goblin Shaman 1",
                "Goblin 2",
                "Goblin Shaman 2",
            ),
        ),
        (
            ("goblin", "goblin", "goblin_warrior", "goblin"),
            ("Goblin 1", "Goblin 2", "Goblin Warrior", "Goblin 3"),
        ),
    ),
)
def test_real_enemy_label_contract_is_preserved(archetype_ids, expected):
    assert _labels(archetype_ids) == expected


def test_dictionary_labeling_matches_counter_reference_for_generated_sequences():
    display_names = ("Goblin", "Goblin Warrior", "Goblin Shaman")
    for length in range(1, 5):
        for names in product(display_names, repeat=length):
            enemies = tuple(SimpleNamespace(display_name=name) for name in names)
            assert Battle._build_enemy_display_labels(enemies) == _counter_reference(
                names
            )


def test_real_battle_construction_preserves_target_ids_and_labels():
    player_state = PlayerState(create_drifter("branoc"))
    enemies = (_enemy("goblin"), _enemy("goblin"), _enemy("goblin_warrior"))

    battle = Battle(player_state, enemies, ui=None, rng=AlwaysOneRng())
    view = battle.current_view()

    assert battle.enemy_target_ids == ("enemy_1", "enemy_2", "enemy_3")
    assert battle.enemy_display_labels == (
        "Goblin 1",
        "Goblin 2",
        "Goblin Warrior",
    )
    assert tuple(enemy.display_label for enemy in view.enemies) == (
        "Goblin 1",
        "Goblin 2",
        "Goblin Warrior",
    )


def test_distinct_same_name_enemies_are_accepted_and_numbered_independently():
    first = _enemy("goblin")
    second = _enemy("goblin")

    battle = Battle(
        PlayerState(create_drifter("branoc")),
        (first, second),
        ui=None,
        rng=AlwaysOneRng(),
    )

    assert first is not second
    assert battle.enemy_display_labels == ("Goblin 1", "Goblin 2")


def test_same_enemy_instance_is_still_rejected():
    enemy = _enemy("goblin")

    with pytest.raises(ValueError, match="same EnemyState"):
        Battle(
            PlayerState(create_drifter("branoc")),
            (enemy, enemy),
            ui=None,
            rng=AlwaysOneRng(),
        )

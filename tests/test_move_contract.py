import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.combat.move import (
    DamageType,
    Move,
    MoveKind,
    ResourceType,
    ScalingAttribute,
    TargetType,
)


def assert_raises(error_type, action):
    try:
        action()
    except error_type as error:
        return error

    raise AssertionError(f"{error_type.__name__} was not raised")


def create_move(**overrides):
    values = {
        "name": "test move",
        "kind": MoveKind.DAMAGE,
        "resource_type": ResourceType.MANA,
        "resource_cost": 3,
        "power": 10,
        "scales_with": (ScalingAttribute.STRENGTH,),
        "accuracy": 90,
        "target": TargetType.ENEMY,
        "damage_type": DamageType.PHYSICAL,
        "mechanic": "test",
        "description": "A test move.",
    }
    values.update(overrides)
    return Move(**values)


def test_valid_move_construction_and_string_value_coercion():
    move = create_move(
        kind="damage",
        resource_type="mana",
        scales_with=("strength",),
        target="enemy",
        damage_type="physical",
    )

    assert move.kind == MoveKind.DAMAGE
    assert move.resource_type == ResourceType.MANA
    assert move.resource_cost == 3
    assert move.scales_with == (ScalingAttribute.STRENGTH,)
    assert move.mana_cost == 3


def test_move_is_immutable():
    move = create_move()

    assert_raises(FrozenInstanceError, lambda: setattr(move, "power", 99))


def test_resource_cost_validation():
    assert create_move(resource_type=ResourceType.NONE, resource_cost=0).mana_cost == 0
    assert_raises(ValueError, lambda: create_move(resource_type=ResourceType.NONE, resource_cost=1))
    assert_raises(ValueError, lambda: create_move(resource_cost=-1))
    assert_raises(TypeError, lambda: create_move(resource_cost=True))
    assert_raises(TypeError, lambda: create_move(resource_cost=1.5))


def test_character_resource_type_is_not_accepted():
    assert_raises(ValueError, lambda: create_move(resource_type="character", resource_cost=3))


def test_super_resource_type_is_valid_and_not_reported_as_mana():
    super_move = create_move(resource_type=ResourceType.SUPER, resource_cost=3)

    assert super_move.resource_type == ResourceType.SUPER
    assert_raises(ValueError, lambda: super_move.mana_cost)


def test_power_and_accuracy_validation():
    assert create_move(power=0).power == 0
    assert create_move(accuracy=0).accuracy == 0
    assert create_move(accuracy=100).accuracy == 100

    assert_raises(ValueError, lambda: create_move(power=-1))
    assert_raises(TypeError, lambda: create_move(power=False))
    assert_raises(ValueError, lambda: create_move(accuracy=101))
    assert_raises(TypeError, lambda: create_move(accuracy=True))


def test_scaling_tuple_validation():
    assert create_move(scales_with=(ScalingAttribute.STRENGTH,)).scales_with == (
        ScalingAttribute.STRENGTH,
    )
    assert create_move(
        scales_with=(ScalingAttribute.INTELLIGENCE, ScalingAttribute.INTUITION),
    ).scales_with == (ScalingAttribute.INTELLIGENCE, ScalingAttribute.INTUITION)
    assert create_move(scales_with=(ScalingAttribute.NONE,)).scales_with == (
        ScalingAttribute.NONE,
    )

    assert_raises(TypeError, lambda: create_move(scales_with=[ScalingAttribute.STRENGTH]))
    assert_raises(ValueError, lambda: create_move(scales_with=()))
    assert_raises(
        ValueError,
        lambda: create_move(scales_with=(ScalingAttribute.STRENGTH, ScalingAttribute.STRENGTH)),
    )
    assert_raises(
        ValueError,
        lambda: create_move(scales_with=(ScalingAttribute.NONE, ScalingAttribute.INTELLIGENCE)),
    )


def test_string_fields_and_enum_validation():
    assert create_move(mechanic=None).mechanic is None

    assert_raises(ValueError, lambda: create_move(name=""))
    assert_raises(TypeError, lambda: create_move(name=None))
    assert_raises(ValueError, lambda: create_move(description=""))
    assert_raises(ValueError, lambda: create_move(mechanic=""))
    assert_raises(ValueError, lambda: create_move(kind="physical_damage"))
    assert_raises(ValueError, lambda: create_move(resource_type="stamina"))
    assert_raises(ValueError, lambda: create_move(target="all"))
    assert_raises(ValueError, lambda: create_move(damage_type="fire"))


if __name__ == "__main__":
    test_valid_move_construction_and_string_value_coercion()
    test_move_is_immutable()
    test_resource_cost_validation()
    test_character_resource_type_is_not_accepted()
    test_super_resource_type_is_valid_and_not_reported_as_mana()
    test_power_and_accuracy_validation()
    test_scaling_tuple_validation()
    test_string_fields_and_enum_validation()
    print("Move contract test passed.")

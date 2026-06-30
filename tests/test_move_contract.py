from dataclasses import FrozenInstanceError

import pytest

from app.combat.move import (
    DamageType,
    Move,
    MoveKind,
    ResourceType,
    ScalingAttribute,
    TargetType,
)


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

    with pytest.raises(FrozenInstanceError):
        setattr(move, "power", 99)


def test_resource_cost_validation():
    assert create_move(resource_type=ResourceType.NONE, resource_cost=0).mana_cost == 0
    with pytest.raises(ValueError):
        create_move(resource_type=ResourceType.NONE, resource_cost=1)
    with pytest.raises(ValueError):
        create_move(resource_cost=-1)
    with pytest.raises(TypeError):
        create_move(resource_cost=True)
    with pytest.raises(TypeError):
        create_move(resource_cost=1.5)


def test_character_resource_type_is_not_accepted():
    with pytest.raises(ValueError):
        create_move(resource_type="character", resource_cost=3)


def test_super_resource_type_is_valid_and_not_reported_as_mana():
    super_move = create_move(resource_type=ResourceType.SUPER, resource_cost=3)

    assert super_move.resource_type == ResourceType.SUPER
    with pytest.raises(ValueError):
        super_move.mana_cost


def test_power_and_accuracy_validation():
    assert create_move(power=0).power == 0
    assert create_move(accuracy=0).accuracy == 0
    assert create_move(accuracy=100).accuracy == 100

    with pytest.raises(ValueError):
        create_move(power=-1)
    with pytest.raises(TypeError):
        create_move(power=False)
    with pytest.raises(ValueError):
        create_move(accuracy=101)
    with pytest.raises(TypeError):
        create_move(accuracy=True)


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

    with pytest.raises(TypeError):
        create_move(scales_with=[ScalingAttribute.STRENGTH])
    with pytest.raises(ValueError):
        create_move(scales_with=())
    with pytest.raises(ValueError):
        create_move(scales_with=(ScalingAttribute.STRENGTH, ScalingAttribute.STRENGTH))
    with pytest.raises(ValueError):
        create_move(scales_with=(ScalingAttribute.NONE, ScalingAttribute.INTELLIGENCE))


def test_string_fields_and_enum_validation():
    assert create_move(mechanic=None).mechanic is None

    with pytest.raises(ValueError):
        create_move(name="")
    with pytest.raises(TypeError):
        create_move(name=None)
    with pytest.raises(ValueError):
        create_move(description="")
    with pytest.raises(ValueError):
        create_move(mechanic="")
    with pytest.raises(ValueError):
        create_move(kind="physical_damage")
    with pytest.raises(ValueError):
        create_move(resource_type="stamina")
    with pytest.raises(ValueError):
        create_move(target="all")
    with pytest.raises(ValueError):
        create_move(damage_type="fire")

import pytest

from dataclasses import FrozenInstanceError

from app.combat.result import MoveResult



def create_result(**overrides):
    values = {
        "accepted": True,
        "hit": True,
        "move_name": "slash",
        "resource_spent": 0,
        "damage": 5,
        "healing": 0,
        "statuses_applied": ("burn",),
        "reason": None,
        "critical": False,
    }
    values.update(overrides)
    return MoveResult(**values)


def test_valid_move_result_construction():
    result = create_result()

    assert result.accepted is True
    assert result.hit is True
    assert result.critical is False
    assert result.move_name == "slash"
    assert result.statuses_applied == ("burn",)
    assert result.reason is None


def test_move_result_is_immutable():
    result = create_result()

    with pytest.raises(FrozenInstanceError):
        setattr(result, "damage", 99)


def test_boolean_fields_must_be_booleans():
    with pytest.raises(TypeError):
        create_result(accepted=1)
    with pytest.raises(TypeError):
        create_result(hit="yes")
    with pytest.raises(TypeError):
        create_result(critical="yes")


def test_numeric_fields_are_nonnegative_integers_and_reject_booleans():
    for field_name in ("resource_spent", "damage", "healing"):
        assert getattr(create_result(**{field_name: 0}), field_name) == 0
        with pytest.raises(ValueError):
            create_result(**{field_name: -1})
        with pytest.raises(TypeError):
            create_result(**{field_name: True})
        with pytest.raises(TypeError):
            create_result(**{field_name: 1.5})


def test_statuses_are_immutable_nonempty_strings():
    result = create_result(statuses_applied=())

    assert result.statuses_applied == ()
    with pytest.raises(TypeError):
        create_result(statuses_applied=["burn"])
    with pytest.raises(ValueError):
        create_result(statuses_applied=("",))
    with pytest.raises(TypeError):
        create_result(statuses_applied=(object(),))


def test_move_name_and_reason_validation():
    assert create_result(reason="insufficient resource").reason == "insufficient resource"
    with pytest.raises(ValueError):
        create_result(move_name="")
    with pytest.raises(TypeError):
        create_result(move_name=None)
    with pytest.raises(ValueError):
        create_result(reason="")
    with pytest.raises(TypeError):
        create_result(reason=1)


def test_structural_contract_allows_future_valid_action_shapes():
    create_result(accepted=False, hit=False, resource_spent=0, damage=0, healing=0, reason="unknown move")
    create_result(accepted=True, hit=False, resource_spent=3, damage=0, healing=0, statuses_applied=())
    create_result(accepted=True, hit=True, resource_spent=2, damage=0, healing=0, statuses_applied=("stun",))
    create_result(accepted=True, hit=True, resource_spent=4, damage=5, healing=5)
    create_result(accepted=True, hit=True, resource_spent=4, damage=7, healing=0, critical=True)

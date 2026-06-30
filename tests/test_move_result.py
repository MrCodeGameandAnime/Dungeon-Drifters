from dataclasses import FrozenInstanceError

from app.combat.result import MoveResult


def assert_raises(error_type, action):
    try:
        action()
    except error_type:
        return

    raise AssertionError(f"{error_type.__name__} was not raised")


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
    }
    values.update(overrides)
    return MoveResult(**values)


def test_valid_move_result_construction():
    result = create_result()

    assert result.accepted is True
    assert result.hit is True
    assert result.move_name == "slash"
    assert result.statuses_applied == ("burn",)
    assert result.reason is None


def test_move_result_is_immutable():
    result = create_result()

    assert_raises(FrozenInstanceError, lambda: setattr(result, "damage", 99))


def test_boolean_fields_must_be_booleans():
    assert_raises(TypeError, lambda: create_result(accepted=1))
    assert_raises(TypeError, lambda: create_result(hit="yes"))


def test_numeric_fields_are_nonnegative_integers_and_reject_booleans():
    for field_name in ("resource_spent", "damage", "healing"):
        assert getattr(create_result(**{field_name: 0}), field_name) == 0
        assert_raises(ValueError, lambda field_name=field_name: create_result(**{field_name: -1}))
        assert_raises(TypeError, lambda field_name=field_name: create_result(**{field_name: True}))
        assert_raises(TypeError, lambda field_name=field_name: create_result(**{field_name: 1.5}))


def test_statuses_are_immutable_nonempty_strings():
    result = create_result(statuses_applied=())

    assert result.statuses_applied == ()
    assert_raises(TypeError, lambda: create_result(statuses_applied=["burn"]))
    assert_raises(ValueError, lambda: create_result(statuses_applied=("",)))
    assert_raises(TypeError, lambda: create_result(statuses_applied=(object(),)))


def test_move_name_and_reason_validation():
    assert create_result(reason="insufficient resource").reason == "insufficient resource"
    assert_raises(ValueError, lambda: create_result(move_name=""))
    assert_raises(TypeError, lambda: create_result(move_name=None))
    assert_raises(ValueError, lambda: create_result(reason=""))
    assert_raises(TypeError, lambda: create_result(reason=1))


def test_structural_contract_allows_future_valid_action_shapes():
    create_result(accepted=False, hit=False, resource_spent=0, damage=0, healing=0, reason="unknown move")
    create_result(accepted=True, hit=False, resource_spent=3, damage=0, healing=0, statuses_applied=())
    create_result(accepted=True, hit=True, resource_spent=2, damage=0, healing=0, statuses_applied=("stun",))
    create_result(accepted=True, hit=True, resource_spent=4, damage=5, healing=5)


if __name__ == "__main__":
    test_valid_move_result_construction()
    test_move_result_is_immutable()
    test_boolean_fields_must_be_booleans()
    test_numeric_fields_are_nonnegative_integers_and_reject_booleans()
    test_statuses_are_immutable_nonempty_strings()
    test_move_name_and_reason_validation()
    test_structural_contract_allows_future_valid_action_shapes()
    print("Move result test passed.")

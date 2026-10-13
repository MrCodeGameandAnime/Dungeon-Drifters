from types import SimpleNamespace

import pytest

from app.persistence.ports import SaveLoadStatus, SavePortError, is_save_port


class CompleteSavePort:
    def save(self, game_state):
        return game_state

    def inspect(self):
        return None

    def load(self):
        return None


def test_none_is_not_a_save_port():
    assert is_save_port(None) is False


def test_object_with_callable_save_port_methods_is_accepted():
    assert is_save_port(CompleteSavePort()) is True


@pytest.mark.parametrize(
    "save_port",
    [
        SimpleNamespace(inspect=lambda: None, load=lambda: None),
        SimpleNamespace(save=lambda game_state: game_state, load=lambda: None),
        SimpleNamespace(save=lambda game_state: game_state, inspect=lambda: None),
    ],
)
def test_save_port_missing_required_method_is_rejected(save_port):
    assert is_save_port(save_port) is False


@pytest.mark.parametrize("attribute", ["save", "inspect", "load"])
def test_save_port_with_non_callable_method_is_rejected(attribute):
    save_port = CompleteSavePort()
    setattr(save_port, attribute, None)

    assert is_save_port(save_port) is False


def test_save_status_distinguishes_success_from_inspection():
    assert SaveLoadStatus.SAVED.value == "saved"
    assert SaveLoadStatus.VALID.value == "valid"


def test_save_port_error_is_a_runtime_error():
    assert issubclass(SavePortError, RuntimeError)

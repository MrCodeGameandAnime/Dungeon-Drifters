import pytest
from types import SimpleNamespace

from app.game.save_contract import (
    SaveLoadStatus as ContractStatus,
    SaveRepositoryError as ContractError,
    is_save_repository,
)
from app.game.save_repository import (
    SaveLoadStatus as RepositoryStatus,
    SaveRepositoryError as RepositoryError,
)


class CompleteRepository:
    def save(self, game_state):
        return game_state

    def inspect(self):
        return None

    def load(self):
        return None


def test_none_is_not_a_save_repository():
    assert is_save_repository(None) is False


def test_repository_with_callable_persistence_methods_is_accepted():
    assert is_save_repository(CompleteRepository()) is True


@pytest.mark.parametrize(
    "repository",
    [
        SimpleNamespace(inspect=lambda: None, load=lambda: None),
        SimpleNamespace(save=lambda game_state: game_state, load=lambda: None),
        SimpleNamespace(save=lambda game_state: game_state, inspect=lambda: None),
    ],
)
def test_repository_missing_required_method_is_rejected(repository):
    assert is_save_repository(repository) is False


@pytest.mark.parametrize("attribute", ["save", "inspect", "load"])
def test_repository_with_non_callable_method_is_rejected(attribute):
    repository = CompleteRepository()
    setattr(repository, attribute, None)

    assert is_save_repository(repository) is False


def test_repository_re_exports_contract_types():
    assert RepositoryStatus is ContractStatus
    assert RepositoryError is ContractError

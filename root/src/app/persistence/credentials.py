"""Credential storage capability, intentionally distinct from ProfileStore."""

from typing import Protocol

from app.persistence.account import AccountCredentials
from app.runtime_contracts import has_required_members


class CredentialStore(Protocol):
    def load(self) -> AccountCredentials | None: ...

    def save(self, credentials: AccountCredentials) -> None: ...

    def clear(self) -> None: ...


_CREDENTIAL_STORE_METHODS = ("load", "save", "clear")


def is_credential_store(value):
    return has_required_members(
        value,
        _CREDENTIAL_STORE_METHODS,
        _CREDENTIAL_STORE_METHODS,
    )


__all__ = ["CredentialStore", "is_credential_store"]

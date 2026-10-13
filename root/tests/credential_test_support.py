from app.persistence.account import AccountCredentials


class MemoryCredentialStore:
    def __init__(self):
        self._credentials = None

    def load(self):
        return self._credentials

    def save(self, credentials):
        if not isinstance(credentials, AccountCredentials):
            raise TypeError("credentials must be AccountCredentials")
        self._credentials = credentials

    def clear(self):
        self._credentials = None

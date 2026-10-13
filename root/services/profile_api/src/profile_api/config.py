from dataclasses import dataclass
from datetime import timedelta
import os


@dataclass(frozen=True)
class Settings:
    access_token_ttl: timedelta = timedelta(minutes=15)
    refresh_token_ttl: timedelta = timedelta(days=30)

    @classmethod
    def from_environment(cls):
        return cls(
            access_token_ttl=timedelta(
                seconds=int(os.getenv("DD_ACCESS_TOKEN_TTL_SECONDS", "900"))
            ),
            refresh_token_ttl=timedelta(
                seconds=int(os.getenv("DD_REFRESH_TOKEN_TTL_SECONDS", "2592000"))
            ),
        )

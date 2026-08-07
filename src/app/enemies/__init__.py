from app.enemies.definition import (
    Enemy,
    EnemyBehavior,
    EnemyCapability,
    EnemyRank,
    EnemyRole,
)
from app.enemies.state import EnemyState

__all__ = [
    "Enemy",
    "EnemyBehavior",
    "EnemyCapability",
    "EnemyRank",
    "EnemyRole",
    "EnemyState",
    "create_enemy_definition",
    "create_enemy_state",
]


def __getattr__(name):
    if name in {"create_enemy_definition", "create_enemy_state"}:
        from app.enemies import factory

        return getattr(factory, name)
    raise AttributeError(name)

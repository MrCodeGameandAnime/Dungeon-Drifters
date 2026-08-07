"""Public content-authoring facade."""


__all__ = [
    "ENEMY_SPECS",
    "EnemySpec",
    "StatBlockSpec",
    "create_enemy_definition",
    "create_enemy_state",
    "get_enemy_spec",
]


def __getattr__(name):
    if name in {"EnemySpec", "StatBlockSpec"}:
        from app.content.enemy_spec import EnemySpec, StatBlockSpec

        return {"EnemySpec": EnemySpec, "StatBlockSpec": StatBlockSpec}[name]
    if name in {
        "ENEMY_SPECS",
        "create_enemy_definition",
        "create_enemy_state",
        "get_enemy_spec",
    }:
        from app.content import catalog

        return getattr(catalog, name)
    raise AttributeError(name)

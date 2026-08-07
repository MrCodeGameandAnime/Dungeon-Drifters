"""Generated content imports. Do not edit by hand."""

from app.content.enemies.goblin.enemy import ENEMY as goblin_enemy
from app.content.enemies.goblin_elite.enemy import ENEMY as goblin_elite_enemy
from app.content.enemies.goblin_lord.enemy import ENEMY as goblin_lord_enemy
from app.content.enemies.goblin_shaman.enemy import ENEMY as goblin_shaman_enemy
from app.content.enemies.goblin_warrior.enemy import ENEMY as goblin_warrior_enemy


GENERATED_ENEMY_SPECS = (
    ("goblin", goblin_enemy),
    ("goblin_elite", goblin_elite_enemy),
    ("goblin_lord", goblin_lord_enemy),
    ("goblin_shaman", goblin_shaman_enemy),
    ("goblin_warrior", goblin_warrior_enemy),
)


__all__ = ["GENERATED_ENEMY_SPECS"]

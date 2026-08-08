"""Generated content imports. Do not edit by hand."""

from app.content.enemies.goblin.enemy import ENEMY as goblin_enemy
from app.content.enemies.goblin_elite.enemy import ENEMY as goblin_elite_enemy
from app.content.enemies.goblin_lord.enemy import ENEMY as goblin_lord_enemy
from app.content.enemies.goblin_shaman.enemy import ENEMY as goblin_shaman_enemy
from app.content.enemies.goblin_warrior.enemy import ENEMY as goblin_warrior_enemy
from app.content.weapons.needle_of_plain_iron.weapon import WEAPON as needle_of_plain_iron_weapon
from app.content.weapons.sathren.weapon import WEAPON as sathren_weapon
from app.content.weapons.sky_needle.weapon import WEAPON as sky_needle_weapon
from app.content.weapons.sunder_spire.weapon import WEAPON as sunder_spire_weapon
from app.content.drifters.azhvielle.drifter import DRIFTER as azhvielle_drifter
from app.content.drifters.branoc.drifter import DRIFTER as branoc_drifter
from app.content.drifters.joruun.drifter import DRIFTER as joruun_drifter
from app.content.drifters.zhaivra.drifter import DRIFTER as zhaivra_drifter


GENERATED_ENEMY_SPECS = (
    ("goblin", goblin_enemy),
    ("goblin_elite", goblin_elite_enemy),
    ("goblin_lord", goblin_lord_enemy),
    ("goblin_shaman", goblin_shaman_enemy),
    ("goblin_warrior", goblin_warrior_enemy),
)


GENERATED_WEAPON_SPECS = (
    ("needle_of_plain_iron", needle_of_plain_iron_weapon),
    ("sathren", sathren_weapon),
    ("sky_needle", sky_needle_weapon),
    ("sunder_spire", sunder_spire_weapon),
)


GENERATED_DRIFTER_SPECS = (
    ("azhvielle", azhvielle_drifter),
    ("branoc", branoc_drifter),
    ("joruun", joruun_drifter),
    ("zhaivra", zhaivra_drifter),
)


__all__ = [
    "GENERATED_DRIFTER_SPECS",
    "GENERATED_ENEMY_SPECS",
    "GENERATED_WEAPON_SPECS",
]

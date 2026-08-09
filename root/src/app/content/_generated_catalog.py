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
from app.content.encounters.surface_elite_patrol.encounter import ENCOUNTER as surface_elite_patrol_encounter
from app.content.encounters.surface_goblin_lord.encounter import ENCOUNTER as surface_goblin_lord_encounter
from app.content.encounters.surface_goblin_pair.encounter import ENCOUNTER as surface_goblin_pair_encounter
from app.content.encounters.surface_goblin_solo.encounter import ENCOUNTER as surface_goblin_solo_encounter
from app.content.encounters.surface_shaman_pair.encounter import ENCOUNTER as surface_shaman_pair_encounter
from app.content.encounters.surface_shaman_solo.encounter import ENCOUNTER as surface_shaman_solo_encounter
from app.content.encounters.surface_warrior_pair.encounter import ENCOUNTER as surface_warrior_pair_encounter
from app.content.encounters.surface_warrior_solo.encounter import ENCOUNTER as surface_warrior_solo_encounter
from app.content.routes.surface.route import ROUTE as surface_route


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


GENERATED_ENCOUNTER_SPECS = (
    ("surface_elite_patrol", surface_elite_patrol_encounter),
    ("surface_goblin_lord", surface_goblin_lord_encounter),
    ("surface_goblin_pair", surface_goblin_pair_encounter),
    ("surface_goblin_solo", surface_goblin_solo_encounter),
    ("surface_shaman_pair", surface_shaman_pair_encounter),
    ("surface_shaman_solo", surface_shaman_solo_encounter),
    ("surface_warrior_pair", surface_warrior_pair_encounter),
    ("surface_warrior_solo", surface_warrior_solo_encounter),
)


GENERATED_ROUTE_SPECS = (
    ("surface", surface_route),
)


__all__ = [
    "GENERATED_DRIFTER_SPECS",
    "GENERATED_ENCOUNTER_SPECS",
    "GENERATED_ENEMY_SPECS",
    "GENERATED_ROUTE_SPECS",
    "GENERATED_WEAPON_SPECS",
]

from app.enemies.definition import Enemy, EnemyBehavior, EnemyCapability, EnemyRank, EnemyRole
from app.enemies.goblin_elite.moves import create_goblin_elite_moves


class GoblinElite(Enemy):
    def __init__(self):
        super().__init__(
            strn=8, con=7, intl=2, dex=5, spirit=3, intuition=4,
            hp=130, mana=0, name="Goblin Elite", archetype_id="goblin_elite",
            rank=EnemyRank.ELITE, role=EnemyRole.BRUTE,
            behavior=EnemyBehavior.AGGRESSIVE,
            capabilities=(EnemyCapability.BASIC_ATTACKS,),
            combat_moves=create_goblin_elite_moves(),
        )

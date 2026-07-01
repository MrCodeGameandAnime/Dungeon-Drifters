from app.combat.enemy import Enemy, EnemyBehavior, EnemyCapability, EnemyRank, EnemyRole
from app.combat.enemies.goblin.moves import create_goblin_moves


class Goblin(Enemy):
    def __init__(self):
        super().__init__(
            strn=3,
            con=2,
            intl=1,
            dex=1,
            hp=60,
            mana=0,
            name="Goblin",
            archetype_id="goblin",
            rank=EnemyRank.COMMON,
            role=EnemyRole.MELEE_SKIRMISHER,
            behavior=EnemyBehavior.AGGRESSIVE,
            capabilities=(EnemyCapability.BASIC_ATTACKS,),
            combat_moves=create_goblin_moves())

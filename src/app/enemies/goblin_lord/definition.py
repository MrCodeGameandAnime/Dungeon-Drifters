from app.enemies.definition import Enemy, EnemyBehavior, EnemyCapability, EnemyRank, EnemyRole
from app.enemies.goblin_lord.moves import create_goblin_lord_moves


class GoblinLord(Enemy):
    def __init__(self):
        super().__init__(
            strn=11, con=10, intl=7, dex=6, spirit=7, intuition=9,
            hp=220, mana=30, exp_reward=200, gold_reward=10,
            name="Goblin Lord", archetype_id="goblin_lord",
            rank=EnemyRank.BOSS, role=EnemyRole.BOSS,
            behavior=EnemyBehavior.AGGRESSIVE,
            capabilities=(EnemyCapability.BASIC_ATTACKS, EnemyCapability.MAGIC),
            combat_moves=create_goblin_lord_moves(),
        )

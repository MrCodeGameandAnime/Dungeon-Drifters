from app.enemies.definition import Enemy, EnemyBehavior, EnemyCapability, EnemyRank, EnemyRole
from app.enemies.goblin_warrior.moves import create_goblin_warrior_moves


class GoblinWarrior(Enemy):
    def __init__(self):
        super().__init__(
            strn=5, con=4, intl=1, dex=2, spirit=1, intuition=2,
            hp=85, mana=0, name="Goblin Warrior", archetype_id="goblin_warrior",
            exp_reward=60, gold_reward=5,
            rank=EnemyRank.COMMON, role=EnemyRole.BRUTE,
            behavior=EnemyBehavior.AGGRESSIVE,
            capabilities=(EnemyCapability.BASIC_ATTACKS,),
            combat_moves=create_goblin_warrior_moves(),
        )

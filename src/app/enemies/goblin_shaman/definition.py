from app.enemies.definition import Enemy, EnemyBehavior, EnemyCapability, EnemyRank, EnemyRole
from app.enemies.goblin_shaman.moves import create_goblin_shaman_moves


class GoblinShaman(Enemy):
    def __init__(self):
        super().__init__(
            strn=1, con=2, intl=6, dex=3, spirit=5, intuition=4,
            hp=65, mana=25, name="Goblin Shaman", archetype_id="goblin_shaman",
            exp_reward=90, gold_reward=7,
            rank=EnemyRank.SPECIALIST, role=EnemyRole.CASTER,
            behavior=EnemyBehavior.AGGRESSIVE,
            capabilities=(EnemyCapability.BASIC_ATTACKS, EnemyCapability.MAGIC),
            combat_moves=create_goblin_shaman_moves(),
        )

from app.combat.enemy import Enemy
from app.combat.enemies.goblin.moves import create_goblin_moves


class Goblin(Enemy):
    def __init__(self):
        super().__init__(
            strn=3,
            con=2,
            intl=1,
            dex=1,
            hp=60,
            mana=10,
            name="Goblin",
            combat_moves=create_goblin_moves())


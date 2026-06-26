class Enemy:
    def __init__(self, strn, con, intl, dex, hp, mana, name, moves):
        self.strength = strn
        self.constitution = con
        self.intelligence = intl
        self.dexterity = dex
        self.hp = hp
        self.mana = mana
        self.name = name
        self.moves = moves
        self.level = 1
        self.exp = 0


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
            moves={1: 'slash', 2: 'jumping slash', 3: 'suplex'})


class Orc(Enemy):
    def __init__(self):
        super().__init__(
            strn=7,
            con=5,
            intl=1,
            dex=1,
            hp=60,
            mana=10,
            name="Orc",
            moves={1: 'slash', 2: 'jumping slash', 3: 'suplex'})


class SkeletonArcher(Enemy):
    def __init__(self):
        super().__init__(
            strn=7,
            con=5,
            intl=1,
            dex=1,
            hp=60,
            mana=10,
            name="Skeleton Archer",
            moves={1: 'slash', 2: 'jumping slash', 3: 'suplex'})


class Zombie(Enemy):
    def __init__(self):
        super().__init__(
            strn=7,
            con=5,
            intl=1,
            dex=1,
            hp=60,
            mana=10,
            name="Zombie",
            moves={1: 'slash', 2: 'jumping slash', 3: 'suplex'})


class SnakeLord(Enemy):
    def __init__(self):
        super().__init__(
            strn=7,
            con=5,
            intl=1,
            dex=1,
            hp=60,
            mana=10,
            name="Snake Lord",
            moves={1: 'slash', 2: 'jumping slash', 3: 'suplex'})

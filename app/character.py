from dataclasses import dataclass


@dataclass(frozen=True)
class Move:
    name: str
    kind: str
    mana_cost: int
    power: int
    scales_with: str
    accuracy: int
    target: str
    mechanic: str
    description: str


class Character:
    def __init__(
            self,
            strn,
            con,
            intl,
            dex,
            char,
            hp,
            mana,
            name,
            moves,
            combat_moves=None,
            class_mechanic=None):
        self.strength = strn
        self.constitution = con
        self.intelligence = intl
        self.dexterity = dex
        self.charisma = char
        self.hp = hp
        self.mana = mana
        self.exp = 0
        self.name = name
        self.level = 1
        self.moves = moves
        self.combat_moves = combat_moves or []
        self.class_mechanic = class_mechanic or {}


class Brawler(Character):
    def __init__(self):
        super().__init__(
            strn=7,
            con=5,
            intl=1,
            dex=1,
            char=1,
            hp=60,
            mana=10,
            name="Brawler",
            moves={1: 'slash', 2: 'jumping slash', 3: 'suplex'},
            combat_moves=[
                Move(
                    name='slash',
                    kind='physical_damage',
                    mana_cost=0,
                    power=9,
                    scales_with='strength',
                    accuracy=92,
                    target='enemy',
                    mechanic='combo_builder',
                    description='A reliable close-range strike that builds momentum.'),
                Move(
                    name='jumping slash',
                    kind='physical_damage',
                    mana_cost=3,
                    power=14,
                    scales_with='strength',
                    accuracy=82,
                    target='enemy',
                    mechanic='combo_spender',
                    description='A risky leaping attack that hits harder after momentum is built.'),
                Move(
                    name='suplex',
                    kind='physical_damage_control',
                    mana_cost=5,
                    power=18,
                    scales_with='strength',
                    accuracy=75,
                    target='enemy',
                    mechanic='stagger',
                    description='A brutal throw that can stagger a weakened foe.'),
            ],
            class_mechanic={
                'name': 'Momentum',
                'resource': 'momentum',
                'description': 'Basic hits build momentum; heavy techniques spend it for burst damage.',
            })


class BlackMage(Character):
    def __init__(self):
        super().__init__(
            strn=1,
            con=2,
            intl=7,
            dex=2,
            char=3,
            hp=30,
            mana=70,
            name="Black Mage",
            moves={1: 'fireball', 2: 'heal', 3: 'thunderbolt'},
            combat_moves=[
                Move(
                    name='fireball',
                    kind='magic_damage',
                    mana_cost=8,
                    power=14,
                    scales_with='intelligence',
                    accuracy=88,
                    target='enemy',
                    mechanic='burn',
                    description='A direct fire spell with a chance to leave burning damage later.'),
                Move(
                    name='heal',
                    kind='healing',
                    mana_cost=10,
                    power=12,
                    scales_with='intelligence',
                    accuracy=100,
                    target='self',
                    mechanic='arcane_recovery',
                    description='Restores health instead of damaging the enemy.'),
                Move(
                    name='thunderbolt',
                    kind='magic_damage',
                    mana_cost=14,
                    power=20,
                    scales_with='intelligence',
                    accuracy=78,
                    target='enemy',
                    mechanic='shock',
                    description='A volatile lightning spell with high damage and lower accuracy.'),
            ],
            class_mechanic={
                'name': 'Arcane Focus',
                'resource': 'mana',
                'description': 'Spells spend mana and scale primarily from intelligence.',
            })  # ice shield


class RogueArcher(Character):
    def __init__(self):
        super().__init__(
            strn=2,
            con=3,
            intl=2,
            dex=7,
            char=1,
            hp=45,
            mana=20,
            name="Rogue Archer",
            moves={1: 'deadshot', 2: 'triple shot', 3: 'rain of arrows', 4: 'flaming arrow'},
            combat_moves=[
                Move(
                    name='deadshot',
                    kind='precision_damage',
                    mana_cost=4,
                    power=12,
                    scales_with='dexterity',
                    accuracy=95,
                    target='enemy',
                    mechanic='crit_bonus',
                    description='A precise shot with increased critical potential.'),
                Move(
                    name='triple shot',
                    kind='multi_hit_damage',
                    mana_cost=6,
                    power=6,
                    scales_with='dexterity',
                    accuracy=86,
                    target='enemy',
                    mechanic='multi_hit',
                    description='Fires three lighter shots that can each contribute damage.'),
                Move(
                    name='rain of arrows',
                    kind='area_damage',
                    mana_cost=8,
                    power=10,
                    scales_with='dexterity',
                    accuracy=80,
                    target='enemy',
                    mechanic='volley',
                    description='A broad volley designed for future multi-enemy encounters.'),
                Move(
                    name='flaming arrow',
                    kind='hybrid_damage',
                    mana_cost=7,
                    power=13,
                    scales_with='dexterity',
                    accuracy=84,
                    target='enemy',
                    mechanic='burn',
                    description='A dexterous shot with a fire effect hook for later status damage.'),
            ],
            class_mechanic={
                'name': 'Precision',
                'resource': 'focus',
                'description': 'High dexterity supports accuracy, critical hits, and multi-hit attacks.',
            })


class Monk(Character):
    def __init__(self):
        super().__init__(
            strn=4,
            con=4,
            intl=2,
            dex=3,
            char=2,
            hp=60,
            mana=20,
            name="Monk",
            moves={1: 'Bring The Horse To Water',
                      2: 'Sweep The Leaves',
                      3: '5-foot punch',
                      4: 'Waki Gamae Kamae Kata',
                      5: 'Carry Water'},
            combat_moves=[
                Move(
                    name='Bring The Horse To Water',
                    kind='physical_damage_control',
                    mana_cost=3,
                    power=10,
                    scales_with='strength',
                    accuracy=90,
                    target='enemy',
                    mechanic='brace',
                    description='Braces the staff and pulls the target into the strike.'),
                Move(
                    name='Sweep The Leaves',
                    kind='physical_damage_control',
                    mana_cost=4,
                    power=11,
                    scales_with='dexterity',
                    accuracy=88,
                    target='enemy',
                    mechanic='trip',
                    description='A low strike that can knock the enemy off balance.'),
                Move(
                    name='5-foot punch',
                    kind='ki_damage',
                    mana_cost=5,
                    power=13,
                    scales_with='strength',
                    accuracy=86,
                    target='enemy',
                    mechanic='ki_burst',
                    description='A focused staff thrust that channels Ki through impact.'),
                Move(
                    name='Waki Gamae Kamae Kata',
                    kind='charged_damage',
                    mana_cost=8,
                    power=20,
                    scales_with='constitution',
                    accuracy=76,
                    target='enemy',
                    mechanic='charged_counter',
                    description='A committed overhead form best used after bracing or defending.'),
                Move(
                    name='Carry Water',
                    kind='finisher_damage',
                    mana_cost=10,
                    power=24,
                    scales_with='strength',
                    accuracy=72,
                    target='enemy',
                    mechanic='prone_finisher',
                    description='A heavy finishing maneuver against a vulnerable or prone foe.'),
            ],
            class_mechanic={
                'name': 'Ki Forms',
                'resource': 'ki',
                'description': 'Monk techniques combine positioning, balance, and Ki setup effects.',
            })
        # Bring The Horse To Water:
        # brace the quarterstaff (think: set spear vs charge) and pull the target's head into it.
        #
        # Sweep The Leaves:
        # low strike to the shin or foot, could also be a shove (trip) attack.
        #
        # 5-foot punch:
        # straight thrust into the stomach, playing on the name of the 5-inch punch from Jeet Kune Do
        #
        # Waki Gamae Kamae Kata (Wah-Kee Gah-May Ka-May Ka-Ta):
        # a strike from holding the quarterstaff overhead with both hands at the bottom.
        # Best when done at the end of a charge or after defending for a turn (to charge up!)
        #
        # Carry Water:
        # execute a fireman's carry maneuver on the quarterstaff against a prone enemy,
        # using both rotational force and adding your own weight to maximize the blow.


class Level:
    def increase_level(self):
        pass


class Health:
    def increase_health(self):
        pass

    def decrease_health(self):
        pass


class Mana:
    def increase_mana(self):
        pass

    def decrease_mana(self):
        pass

    def mana_pool(self):
        pass


class Stats:
    def attack(self):
        pass

    def defense(self):
        pass

    def health(self):
        pass

    def mana(self):
        pass

    def luck(self):
        pass


class Exp:
    def increase_exp(self):
        pass

    def exp_pool(self):
        pass

from app.player import progression
from app.player import resources
from app.player import stats
from app.player.loadouts import azhvielle
from app.player.loadouts import branoc
from app.player.loadouts import joruun
from app.player.loadouts import zhaivra


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
        self.name = name
        self.moves = dict(moves)
        self.combat_moves = list(combat_moves or [])
        self.class_mechanic = dict(class_mechanic or {})
        self.profile = None
        self.stats = stats.Stats(self)
        self.health = resources.Health(maximum=hp)
        self.mana_resource = resources.Mana(maximum=mana)
        self.level_state = progression.Level()
        self.exp_state = progression.Exp(self.level_state)

    @property
    def archetype_name(self):
        return self.name

    @property
    def display_name(self):
        if self.profile is not None:
            return self.profile.short_name
        return self.name

    @property
    def full_display_name(self):
        if self.profile is not None:
            return self.profile.display_name
        return self.name

    @property
    def hp(self):
        return self.health.current

    @hp.setter
    def hp(self, value):
        self.health.current = self.health.clamp(value)

    @property
    def mana(self):
        return self.mana_resource.current

    @mana.setter
    def mana(self, value):
        self.mana_resource.current = self.mana_resource.clamp(value)

    @property
    def level(self):
        return self.level_state.current

    @level.setter
    def level(self, value):
        self.level_state.current = max(1, int(value))

    @property
    def exp(self):
        return self.exp_state.current

    @exp.setter
    def exp(self, value):
        self.exp_state.current = max(0, int(value))


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
            moves=branoc.create_legacy_moves(),
            combat_moves=branoc.create_combat_moves(),
            class_mechanic=branoc.create_class_mechanic())


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
            moves=azhvielle.create_legacy_moves(),
            combat_moves=azhvielle.create_combat_moves(),
            class_mechanic=azhvielle.create_class_mechanic())


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
            moves=zhaivra.create_legacy_moves(),
            combat_moves=zhaivra.create_combat_moves(),
            class_mechanic=zhaivra.create_class_mechanic())


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
            moves=joruun.create_legacy_moves(),
            combat_moves=joruun.create_combat_moves(),
            class_mechanic=joruun.create_class_mechanic())

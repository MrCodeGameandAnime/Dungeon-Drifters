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
            constitution,
            spirit,
            intelligence,
            strength,
            dexterity,
            intuition,
            hp,
            mana,
            name,
            moves,
            combat_moves=None,
            class_mechanic=None):
        self.permanent_stats = stats.PermanentStats(
            constitution=constitution,
            spirit=spirit,
            intelligence=intelligence,
            strength=strength,
            dexterity=dexterity,
            intuition=intuition,
        )
        if self.permanent_stats.total != 60:
            raise ValueError("Level 1 archetype stat total must be 60")

        self.name = name
        self.moves = dict(moves)
        self.combat_moves = list(combat_moves or [])
        self.class_mechanic = dict(class_mechanic or {})
        self.profile = None
        self.stats = stats.Stats(self.permanent_stats)
        self.health = resources.Health(maximum=hp)
        self.mana_resource = resources.Mana(maximum=mana)
        self.level_state = progression.Level()
        self.exp_state = progression.Exp(self.level_state)

    @property
    def constitution(self):
        return self.permanent_stats.constitution

    @constitution.setter
    def constitution(self, value):
        self.permanent_stats.set_stat("constitution", value)

    @property
    def spirit(self):
        return self.permanent_stats.spirit

    @spirit.setter
    def spirit(self, value):
        self.permanent_stats.set_stat("spirit", value)

    @property
    def intelligence(self):
        return self.permanent_stats.intelligence

    @intelligence.setter
    def intelligence(self, value):
        self.permanent_stats.set_stat("intelligence", value)

    @property
    def strength(self):
        return self.permanent_stats.strength

    @strength.setter
    def strength(self, value):
        self.permanent_stats.set_stat("strength", value)

    @property
    def dexterity(self):
        return self.permanent_stats.dexterity

    @dexterity.setter
    def dexterity(self, value):
        self.permanent_stats.set_stat("dexterity", value)

    @property
    def intuition(self):
        return self.permanent_stats.intuition

    @intuition.setter
    def intuition(self, value):
        self.permanent_stats.set_stat("intuition", value)

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
            constitution=14,
            spirit=6,
            intelligence=5,
            strength=15,
            dexterity=10,
            intuition=10,
            hp=60,
            mana=10,
            name="Brawler",
            moves=branoc.create_legacy_moves(),
            combat_moves=branoc.create_combat_moves(),
            class_mechanic=branoc.create_class_mechanic())


class BlackMage(Character):
    def __init__(self):
        super().__init__(
            constitution=7,
            spirit=13,
            intelligence=15,
            strength=5,
            dexterity=8,
            intuition=12,
            hp=30,
            mana=70,
            name="Black Mage",
            moves=azhvielle.create_legacy_moves(),
            combat_moves=azhvielle.create_combat_moves(),
            class_mechanic=azhvielle.create_class_mechanic())


class RogueArcher(Character):
    def __init__(self):
        super().__init__(
            constitution=8,
            spirit=7,
            intelligence=10,
            strength=6,
            dexterity=15,
            intuition=14,
            hp=45,
            mana=20,
            name="Rogue Archer",
            moves=zhaivra.create_legacy_moves(),
            combat_moves=zhaivra.create_combat_moves(),
            class_mechanic=zhaivra.create_class_mechanic())


class Monk(Character):
    def __init__(self):
        super().__init__(
            constitution=10,
            spirit=10,
            intelligence=13,
            strength=7,
            dexterity=12,
            intuition=8,
            hp=60,
            mana=20,
            name="Monk",
            moves=joruun.create_legacy_moves(),
            combat_moves=joruun.create_combat_moves(),
            class_mechanic=joruun.create_class_mechanic())

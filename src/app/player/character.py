from app.player import progression
from app.player import resources
from app.player import scaling
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
            name,
            moves,
            combat_moves=None,
            class_mechanic=None,
            starting_equipment=None,
            starting_run_inventory=None,
            starting_prepared_payloads=None):
        self.permanent_stats = stats.PermanentStats(
            constitution=constitution,
            spirit=spirit,
            intelligence=intelligence,
            strength=strength,
            dexterity=dexterity,
            intuition=intuition,
        )

        self.name = name
        self.moves = dict(moves)
        self.combat_moves = list(combat_moves or [])
        self.class_mechanic = dict(class_mechanic or {})
        self.starting_equipment = dict(starting_equipment or {})
        self.starting_run_inventory = dict(starting_run_inventory or {})
        self.starting_prepared_payloads = dict(starting_prepared_payloads or {})
        self.profile = None
        self.level_state = progression.Level()
        self.stats = stats.Stats(self.permanent_stats)
        self.health = resources.Health(
            maximum=scaling.maximum_hp_from_constitution(
                self.permanent_stats.constitution,
                level=self.level_state.current,
            )
        )
        self.mana_resource = resources.Mana(
            maximum=scaling.maximum_mana_from_spirit(
                self.permanent_stats.spirit,
                level=self.level_state.current,
            )
        )
        self.exp_state = progression.Exp(self.level_state)

    def recalculate_resource_maximums(self, increase_current=False):
        new_health_maximum = scaling.maximum_hp_from_constitution(
            self.permanent_stats.constitution,
            level=self.level_state.current,
        )
        new_mana_maximum = scaling.maximum_mana_from_spirit(
            self.permanent_stats.spirit,
            level=self.level_state.current,
        )

        self._set_resource_maximum(
            self.health,
            new_health_maximum,
            increase_current=increase_current,
        )
        self._set_resource_maximum(
            self.mana_resource,
            new_mana_maximum,
            increase_current=increase_current,
        )

    @staticmethod
    def _set_resource_maximum(resource, new_maximum, *, increase_current):
        delta = new_maximum - resource.maximum
        if delta > 0:
            resource.increase_maximum(delta, increase_current=increase_current)
        elif delta < 0:
            resource.decrease_maximum(-delta)

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
        self.level_state.current = value

    @property
    def exp(self):
        return self.exp_state.current

    @exp.setter
    def exp(self, value):
        self.exp_state.current = max(0, int(value))


def _validate_level_one_stat_total(stat_values):
    total = sum(stat_values.values())
    if total != 60:
        raise ValueError("Level 1 archetype stat total must be 60")

    return stat_values


class Brawler(Character):
    def __init__(self):
        stat_values = _validate_level_one_stat_total(
            branoc.create_starting_stats()
        )
        super().__init__(
            **stat_values,
            name="Brawler",
            moves=branoc.create_legacy_moves(),
            combat_moves=branoc.create_combat_moves(),
            class_mechanic=branoc.create_class_mechanic(),
            starting_equipment={"weapon": branoc.create_starting_weapon()})


class BlackMage(Character):
    def __init__(self):
        stat_values = _validate_level_one_stat_total(
            azhvielle.create_starting_stats()
        )
        super().__init__(
            **stat_values,
            name="Black Mage",
            moves=azhvielle.create_legacy_moves(),
            combat_moves=azhvielle.create_combat_moves(),
            class_mechanic=azhvielle.create_class_mechanic(),
            starting_equipment={"weapon": azhvielle.create_starting_weapon()})


class RogueArcher(Character):
    def __init__(self):
        stat_values = _validate_level_one_stat_total(
            zhaivra.create_starting_stats()
        )
        super().__init__(
            **stat_values,
            name="Rogue Archer",
            moves=zhaivra.create_legacy_moves(),
            combat_moves=zhaivra.create_combat_moves(),
            class_mechanic=zhaivra.create_class_mechanic(),
            starting_run_inventory=zhaivra.create_starting_run_inventory(),
            starting_prepared_payloads=zhaivra.create_starting_prepared_payloads(),
            starting_equipment={"weapon": zhaivra.create_starting_weapon()})


class Monk(Character):
    def __init__(self):
        stat_values = _validate_level_one_stat_total(
            joruun.create_starting_stats()
        )
        super().__init__(
            **stat_values,
            name="Monk",
            moves=joruun.create_legacy_moves(),
            combat_moves=joruun.create_combat_moves(),
            class_mechanic=joruun.create_class_mechanic(),
            starting_equipment={"weapon": joruun.create_starting_weapon()})

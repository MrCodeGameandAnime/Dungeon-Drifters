"""Runtime state for one enemy in one encounter."""

from app.player import resources
from app.player import stats
from app.combat.move import DamageType
from app.enemies.definition import EnemyCapability
from app.enemies.validation import validate_enemy_tier


class EnemyState:
    def __init__(self, enemy_definition, tier=0):
        self._definition = enemy_definition
        self._tier = validate_enemy_tier(tier)
        self.permanent_stats = stats.PermanentStats(
            constitution=enemy_definition.constitution,
            spirit=enemy_definition.spirit,
            intelligence=enemy_definition.intelligence,
            strength=enemy_definition.strength,
            dexterity=enemy_definition.dexterity,
            intuition=enemy_definition.intuition,
        )
        self.stats = stats.Stats(self.permanent_stats)
        self.health = resources.Health(maximum=enemy_definition.hp)
        self.mana_resource = resources.Mana(maximum=enemy_definition.mana)
        self.super_resource = resources.Super()
        self._combat_moves = tuple(enemy_definition.combat_moves)

    @property
    def definition(self):
        return self._definition

    @property
    def display_name(self):
        return self._definition.name

    @property
    def name(self):
        return self.display_name

    @property
    def archetype_id(self):
        return self._definition.archetype_id

    @property
    def exp_reward(self):
        return self._definition.exp_reward

    @property
    def gold_reward(self):
        return self._definition.gold_reward

    @property
    def tier(self):
        return self._tier

    @property
    def rank(self):
        return self._definition.rank

    @property
    def role(self):
        return self._definition.role

    @property
    def behavior(self):
        return self._definition.behavior

    @property
    def capabilities(self):
        return self._definition.capabilities

    @property
    def generates_super(self):
        return EnemyCapability.SUPER in self.capabilities

    @property
    def can_defend(self):
        return EnemyCapability.DEFEND in self.capabilities

    @property
    def moves(self):
        return {
            index: move.name
            for index, move in enumerate(self._combat_moves, start=1)
        }

    @property
    def combat_moves(self):
        return self._combat_moves

    @property
    def strength(self):
        return self.effective_stat("strength")

    @property
    def constitution(self):
        return self.effective_stat("constitution")

    @property
    def intelligence(self):
        return self.effective_stat("intelligence")

    @property
    def dexterity(self):
        return self.effective_stat("dexterity")

    @property
    def spirit(self):
        return self.effective_stat("spirit")

    @property
    def intuition(self):
        return self.effective_stat("intuition")

    def effective_stat(self, name):
        return self.stats.effective_stat(name)

    def defend_reduction_percent(self, damage_type):
        if damage_type == DamageType.PHYSICAL:
            return 50
        if damage_type == DamageType.MAGICAL:
            return 40
        if damage_type == DamageType.HYBRID:
            return 30

        return 0

    def is_alive(self):
        return self.health.is_alive()

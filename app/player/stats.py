class PermanentStats:
    STAT_NAMES = (
        "constitution",
        "spirit",
        "intelligence",
        "strength",
        "dexterity",
        "intuition",
    )
    MINIMUM = 1
    MAXIMUM = 100

    def __init__(
            self,
            constitution,
            spirit,
            intelligence,
            strength,
            dexterity,
            intuition):
        self._values = {
            "constitution": self._validate_value("constitution", constitution),
            "spirit": self._validate_value("spirit", spirit),
            "intelligence": self._validate_value("intelligence", intelligence),
            "strength": self._validate_value("strength", strength),
            "dexterity": self._validate_value("dexterity", dexterity),
            "intuition": self._validate_value("intuition", intuition),
        }

    def __getattr__(self, name):
        if name in self.STAT_NAMES:
            return self._values[name]

        raise AttributeError(name)

    @property
    def total(self):
        return sum(self._values.values())

    def as_dict(self):
        return {
            name: self._values[name]
            for name in self.STAT_NAMES
        }

    def get_stat(self, name):
        self._validate_stat_name(name)
        return self._values[name]

    def set_stat(self, name, value):
        self._validate_stat_name(name)
        self._values[name] = self._validate_value(name, value)
        return self._values[name]

    def increase_stat(self, name, amount):
        self._validate_stat_name(name)
        amount = self._validate_amount(amount)
        return self.set_stat(name, self._values[name] + amount)

    def decrease_stat(self, name, amount):
        self._validate_stat_name(name)
        amount = self._validate_amount(amount)
        return self.set_stat(name, self._values[name] - amount)

    @classmethod
    def _validate_value(cls, name, value):
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} must be an integer")
        if value < cls.MINIMUM or value > cls.MAXIMUM:
            raise ValueError(f"{name} must be between {cls.MINIMUM} and {cls.MAXIMUM}")

        return value

    @staticmethod
    def _validate_amount(amount):
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise TypeError("stat mutation amount must be an integer")
        if amount < 0:
            raise ValueError("stat mutation amount must not be negative")

        return amount

    @classmethod
    def _validate_stat_name(cls, name):
        if name not in cls.STAT_NAMES:
            raise ValueError(f"invalid stat name: {name}")


class Stats:
    def __init__(self, permanent_stats):
        self.permanent_stats = permanent_stats

    def effective_stat(self, name):
        return self.permanent_stats.get_stat(name)

    @property
    def constitution(self):
        return self.effective_stat("constitution")

    @property
    def spirit(self):
        return self.effective_stat("spirit")

    @property
    def intelligence(self):
        return self.effective_stat("intelligence")

    @property
    def strength(self):
        return self.effective_stat("strength")

    @property
    def dexterity(self):
        return self.effective_stat("dexterity")

    @property
    def intuition(self):
        return self.effective_stat("intuition")

    def as_dict(self):
        return {
            name: self.effective_stat(name)
            for name in PermanentStats.STAT_NAMES
        }

    def attack_power(self):
        return max(0, self.strength * 2 + self.dexterity)

    def defense_rating(self):
        return max(0, self.constitution * 2 + self.dexterity // 2)

    def health_bonus(self):
        return max(0, self.constitution * 5)

    def mana_bonus(self):
        return max(0, self.spirit * 5)

    def luck_rating(self):
        return max(0, self.intuition + self.dexterity // 2)

    def attack(self):
        return self.attack_power()

    def defense(self):
        return self.defense_rating()

    def health(self):
        return self.health_bonus()

    def mana(self):
        return self.mana_bonus()

    def luck(self):
        return self.luck_rating()

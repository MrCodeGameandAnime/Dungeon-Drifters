class Health:
    def __init__(self, maximum, current=None):
        self.maximum = self._validate_maximum(maximum)
        self.current = self.clamp(self.maximum if current is None else current)

    def clamp(self, value):
        return max(0, min(self.maximum, int(value)))

    def heal(self, amount):
        amount = max(0, int(amount))
        self.current = self.clamp(self.current + amount)
        return self.current

    def increase_health(self, amount):
        return self.heal(amount)

    def take_damage(self, amount):
        amount = max(0, int(amount))
        self.current = self.clamp(self.current - amount)
        return self.current

    def decrease_health(self, amount):
        return self.take_damage(amount)

    def is_defeated(self):
        return self.current <= 0

    def is_alive(self):
        return not self.is_defeated()

    def set_maximum(self, maximum):
        self.maximum = self._validate_maximum(maximum)
        self.current = self.clamp(self.current)
        return self.maximum

    def increase_maximum(self, amount, increase_current=False):
        amount = self._validate_amount(amount)
        self.maximum += amount
        if increase_current:
            self.current = self.clamp(self.current + amount)
        return self.maximum

    def decrease_maximum(self, amount):
        amount = self._validate_amount(amount)
        self.maximum = max(0, self.maximum - amount)
        self.current = self.clamp(self.current)
        return self.maximum

    @staticmethod
    def _validate_maximum(maximum):
        if isinstance(maximum, bool) or not isinstance(maximum, int):
            raise TypeError("maximum must be an integer")
        if maximum < 0:
            raise ValueError("maximum must not be negative")

        return maximum

    @staticmethod
    def _validate_amount(amount):
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise TypeError("maximum change amount must be an integer")
        if amount < 0:
            raise ValueError("maximum change amount must not be negative")

        return amount


class Mana:
    def __init__(self, maximum, current=None):
        self.maximum = self._validate_maximum(maximum)
        self.current = self.clamp(self.maximum if current is None else current)

    def clamp(self, value):
        return max(0, min(self.maximum, int(value)))

    def can_afford(self, amount):
        amount = max(0, int(amount))
        return self.current >= amount

    def spend(self, amount):
        amount = max(0, int(amount))
        if not self.can_afford(amount):
            return False

        self.current -= amount
        return True

    def restore(self, amount):
        amount = max(0, int(amount))
        self.current = self.clamp(self.current + amount)
        return self.current

    def increase_mana(self, amount):
        return self.restore(amount)

    def decrease_mana(self, amount):
        return self.spend(amount)

    def mana_pool(self):
        return {
            'current': self.current,
            'maximum': self.maximum,
        }

    def set_maximum(self, maximum):
        self.maximum = self._validate_maximum(maximum)
        self.current = self.clamp(self.current)
        return self.maximum

    def increase_maximum(self, amount, increase_current=False):
        amount = self._validate_amount(amount)
        self.maximum += amount
        if increase_current:
            self.current = self.clamp(self.current + amount)
        return self.maximum

    def decrease_maximum(self, amount):
        amount = self._validate_amount(amount)
        self.maximum = max(0, self.maximum - amount)
        self.current = self.clamp(self.current)
        return self.maximum

    @staticmethod
    def _validate_maximum(maximum):
        if isinstance(maximum, bool) or not isinstance(maximum, int):
            raise TypeError("maximum must be an integer")
        if maximum < 0:
            raise ValueError("maximum must not be negative")

        return maximum

    @staticmethod
    def _validate_amount(amount):
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise TypeError("maximum change amount must be an integer")
        if amount < 0:
            raise ValueError("maximum change amount must not be negative")

        return amount


class Super:
    MAXIMUM = 100
    STARTING_VALUE = 0

    def __init__(self, current=STARTING_VALUE):
        self.maximum = self.MAXIMUM
        self.current = self._validate_current(current)

    def can_afford(self, amount):
        amount = self._validate_amount(amount)
        return self.current >= amount

    def gain(self, amount):
        amount = self._validate_amount(amount)
        self.current = min(self.maximum, self.current + amount)
        return self.current

    def spend(self, amount):
        amount = self._validate_amount(amount)
        if not self.can_afford(amount):
            return False

        self.current -= amount
        return True

    def reset(self):
        self.current = self.STARTING_VALUE
        return self.current

    @classmethod
    def _validate_current(cls, current):
        if isinstance(current, bool) or not isinstance(current, int):
            raise TypeError("super current value must be an integer")
        if current < cls.STARTING_VALUE or current > cls.MAXIMUM:
            raise ValueError(
                f"super current value must be between {cls.STARTING_VALUE} and {cls.MAXIMUM}"
            )

        return current

    @staticmethod
    def _validate_amount(amount):
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise TypeError("super amount must be an integer")
        if amount < 0:
            raise ValueError("super amount must not be negative")

        return amount

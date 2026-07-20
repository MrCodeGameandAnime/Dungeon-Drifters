MINIMUM_LEVEL = 1
MAXIMUM_LEVEL = 250
GROWTH_POINTS_PER_LEVEL = 3


def xp_required_for_next_level(current_level):
    current_level = _validate_level_value(current_level)
    if current_level == MAXIMUM_LEVEL:
        return None

    ramp = max(0, current_level - 10)
    return 20 * (ramp + 5) * (current_level + 30) ** 2 // 961


class Level:
    def __init__(self, current=MINIMUM_LEVEL):
        self._current = _validate_level_value(current)

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, value):
        self._current = _validate_level_value(value)

    @property
    def next_threshold(self):
        return xp_required_for_next_level(self.current)

    def increase_level(self, amount=1):
        amount = _validate_nonnegative_integer("level increase", amount)
        self._current = min(MAXIMUM_LEVEL, self.current + amount)
        return self.current


class Exp:
    def __init__(self, level):
        self.level = level
        self.current = 0

    def exp_pool(self):
        return {
            "current": self.current,
            "level": self.level.current,
            "next_threshold": self.level.next_threshold,
        }

    @staticmethod
    def validate_gain_amount(amount):
        return _validate_nonnegative_integer("experience amount", amount)

    def gain(self, amount):
        amount = self.validate_gain_amount(amount)
        if self.level.current == MAXIMUM_LEVEL:
            self.current = 0
            return 0

        self.current += amount
        levels_gained = 0

        while self.level.current < MAXIMUM_LEVEL:
            threshold = self.level.next_threshold
            if self.current < threshold:
                break

            self.current -= threshold
            self.level.increase_level()
            levels_gained += 1

        if self.level.current == MAXIMUM_LEVEL:
            self.current = 0

        return levels_gained

    def increase_exp(self, amount):
        return self.gain(amount)


def _validate_level_value(value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("level must be an integer")
    if value < MINIMUM_LEVEL or value > MAXIMUM_LEVEL:
        raise ValueError(
            f"level must be between {MINIMUM_LEVEL} and {MAXIMUM_LEVEL}"
        )

    return value


def _validate_nonnegative_integer(name, value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be a nonnegative integer")
    if value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")

    return value

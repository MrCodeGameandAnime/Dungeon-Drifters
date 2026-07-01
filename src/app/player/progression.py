class Level:
    def __init__(self, current=1, base_threshold=100):
        self.current = max(1, int(current))
        self.base_threshold = max(1, int(base_threshold))

    @property
    def next_threshold(self):
        return self.base_threshold * self.current

    def increase_level(self, amount=1):
        amount = max(0, int(amount))
        self.current += amount
        return self.current


class Exp:
    def __init__(self, level):
        self.level = level
        self.current = 0

    def exp_pool(self):
        return {
            'current': self.current,
            'level': self.level.current,
            'next_threshold': self.level.next_threshold,
        }

    def gain(self, amount):
        amount = max(0, int(amount))
        self.current += amount
        levels_gained = 0

        while self.current >= self.level.next_threshold:
            self.current -= self.level.next_threshold
            self.level.increase_level()
            levels_gained += 1

        return levels_gained

    def increase_exp(self, amount):
        return self.gain(amount)

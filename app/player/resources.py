class Health:
    def __init__(self, maximum, current=None):
        self.maximum = max(0, int(maximum))
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


class Mana:
    def __init__(self, maximum, current=None):
        self.maximum = max(0, int(maximum))
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

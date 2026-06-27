class Stats:
    def __init__(self, character):
        self.character = character

    def attack_power(self):
        return max(0, self.character.strength * 2 + self.character.dexterity)

    def defense_rating(self):
        return max(0, self.character.constitution * 2 + self.character.dexterity // 2)

    def health_bonus(self):
        return max(0, self.character.constitution * 5)

    def mana_bonus(self):
        return max(0, self.character.intelligence * 5)

    def luck_rating(self):
        return max(0, self.character.charisma + self.character.dexterity // 2)

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

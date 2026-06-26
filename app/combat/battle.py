import random


class Battle:
    def __init__(self, player_state, foe):
        self.player_state = player_state
        self.player = player_state.character
        self.foe = foe
        self.foe_max_hp = foe.hp
        self.foe_health = foe.hp

    def run(self):
        print(f"\nA {self.foe.name} blocks your path!")

        player_turn = random.randint(1, 2) == 1
        if player_turn:
            print("\nPlayer will go first.")
        else:
            print("\nThe enemy will go first.")

        self.print_health()

        while self.player_state.health.is_alive() and self.foe_health > 0:
            if player_turn:
                self.player_action()
            else:
                self.enemy_action()

            self.print_health()
            player_turn = not player_turn

        return "player" if self.foe_health <= 0 else "enemy"

    def player_action(self):
        moves = list(self.player.moves.values())
        quick_move = moves[0]
        power_move = moves[1] if len(moves) > 1 else moves[0]

        print(f'''
Choose a move:
1. {quick_move} (steady attack)
2. {power_move} (risky heavy attack)
3. Recover (restore health)
        ''')

        while True:
            choice = input("> ").strip().lower()
            if choice in ("1", quick_move.lower()):
                self.attack(self.player, self.foe, quick_move, heavy=False)
                return
            if choice in ("2", power_move.lower()):
                self.attack(self.player, self.foe, power_move, heavy=True)
                return
            if choice in ("3", "recover", "heal"):
                self.heal_player()
                return

            print("That is not a valid move. Please try again.")

    def enemy_action(self):
        if self.foe_health <= self.foe_max_hp // 3 and random.randint(1, 2) == 1:
            heal_amount = random.randint(6, 12) + self.foe.constitution
            self.foe_health = min(self.foe_max_hp, self.foe_health + heal_amount)
            print(f"\nThe {self.foe.name} regroups and recovers {heal_amount} health.")
            return

        moves = list(self.foe.moves.values())
        move = random.choice(moves)
        damage = random.randint(6, 12) + self.foe.strength

        if self.misses():
            print(f"\nThe {self.foe.name} used {move}, but missed!")
            return

        self.player_state.health.take_damage(damage)
        print(f"\nThe {self.foe.name} used {move}. It dealt {damage} damage.")

    def attack(self, attacker, target, move_name, heavy):
        if self.misses():
            print(f"\n{attacker.name} used {move_name}, but missed!")
            return

        if heavy:
            damage = random.randint(8, 20) + attacker.strength
        else:
            damage = random.randint(8, 14) + attacker.strength

        self.foe_health = max(0, self.foe_health - damage)
        print(f"\n{attacker.name} used {move_name}. It dealt {damage} damage to the {target.name}.")

    def heal_player(self):
        heal_amount = random.randint(10, 16) + self.player.constitution
        self.player_state.health.heal(heal_amount)
        print(f"\n{self.player.name} takes a breath and recovers {heal_amount} health.")

    @staticmethod
    def misses():
        return random.randint(1, 5) == 1

    def print_health(self):
        print(f"\n{self.player.name} health: {self.player_state.health.current}/{self.player_state.health.maximum}")
        print(f"{self.foe.name} health: {self.foe_health}/{self.foe_max_hp}")

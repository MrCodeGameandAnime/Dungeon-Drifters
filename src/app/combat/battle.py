import random

from app.combat.combat_state import CombatState
from app.combat.move import TargetType
from app.combat.resolver import CombatResolver


class Battle:
    def __init__(self, player_state, foe, resolver=None):
        self.player_state = player_state
        self.player = player_state.character
        self.foe = foe
        self.combat_state = CombatState()
        self.resolver = resolver or CombatResolver()

    def _player_moves(self):
        return self.player_state.combat_moves

    def _enemy_moves(self):
        return self.foe.combat_moves

    def _complete_accepted_action(self, actor, opposing_combatants, result):
        if result.accepted:
            return self.combat_state.complete_accepted_action(
                actor,
                opposing_combatants,
            )

        return None

    def _player_target_for_move(self, move):
        if move.target == TargetType.ENEMY:
            return self.foe
        if move.target == TargetType.SELF:
            return self.player_state

        raise ValueError(f"Unsupported player move target: {move.target!r}")

    def _resolve_player_move(self, move):
        result = self.resolver.resolve_move(
            self.player_state,
            self._player_target_for_move(move),
            move.name,
            combat_state=self.combat_state,
        )
        self._render_move_result(
            result,
            actor=self.player_state,
            target=self._player_target_for_move(move),
        )
        return result

    def _enemy_target_for_move(self, move):
        if move.target == TargetType.ENEMY:
            return self.player_state
        if move.target == TargetType.SELF:
            return self.foe

        raise ValueError(f"Unsupported enemy move target: {move.target!r}")

    def _resolve_enemy_move(self, move):
        result = self.resolver.resolve_move(
            self.foe,
            self._enemy_target_for_move(move),
            move.name,
            combat_state=self.combat_state,
        )
        self._render_move_result(
            result,
            actor=self.foe,
            target=self._enemy_target_for_move(move),
        )
        return result

    def _render_move_result(self, result, actor, target=None):
        actor_name = actor.display_name
        if not result.accepted:
            print(f"{actor_name} used {result.move_name}, but it failed: {result.reason}.")
            return
        if result.move_name == "Defend":
            print(f"{actor_name} used Defend.")
            self._render_move_result_details(result)
            return
        if not result.hit:
            print(f"{actor_name} used {result.move_name}, but missed.")
            self._render_move_result_details(result)
            return
        if result.damage:
            print(f"{actor_name} used {result.move_name}. It dealt {result.damage} damage.")
            self._render_move_result_details(result)
            return
        if result.healing:
            print(f"{actor_name} used {result.move_name}. It restored {result.healing} health.")
            self._render_move_result_details(result)
            return

        print(f"{actor_name} used {result.move_name}. It resolved.")
        self._render_move_result_details(result)

    @staticmethod
    def _render_move_result_details(result):
        if result.resource_spent:
            print(f"Resource spent: {result.resource_spent}.")
        if result.statuses_applied:
            print(f"Statuses applied: {', '.join(result.statuses_applied)}.")

    def run(self):
        print(f"\nA {self.foe.display_name} blocks your path!")

        player_turn = random.randint(1, 2) == 1
        if player_turn:
            print("\nPlayer will go first.")
        else:
            print("\nThe enemy will go first.")

        self.print_health()

        while self.player_state.is_alive() and self.foe.is_alive():
            if player_turn:
                action_accepted = self.player_action()
            else:
                action_accepted = self.enemy_action()

            if action_accepted:
                self.print_health()
                player_turn = not player_turn

        return "player" if not self.foe.is_alive() else "enemy"

    def player_action(self):
        while True:
            print('''
Choose an action:
1. Attack
2. Defend
3. Items
4. Super
            ''')
            choice = input("> ").strip().lower()
            if choice in ("1", "attack"):
                if self._player_attack_menu():
                    return True
                continue
            if choice in ("2", "defend"):
                result = self.resolver.resolve_defend(
                    self.player_state,
                    self.combat_state,
                )
                self._render_move_result(result, actor=self.player_state)
                if result.accepted:
                    self._complete_accepted_action(
                        self.player_state,
                        (self.foe,),
                        result,
                    )
                    return True
                continue
            if choice in ("3", "items"):
                print("Items are not available yet.")
                continue
            if choice in ("4", "super"):
                if self._player_super_menu():
                    return True
                continue

            print("That is not a valid move. Please try again.")

    def _player_attack_menu(self):
        moves = [
            move
            for move in self._player_moves()
            if move.resource_type.value != "super"
        ]

        while True:
            print("\nChoose an attack:")
            for index, move in enumerate(moves, start=1):
                print(
                    f"{index}. {move.name} "
                    f"[{move.resource_type.value} {move.resource_cost}] - "
                    f"{move.description}"
                )
            print("0. Back")

            choice = input("> ").strip().lower()
            if choice == "0":
                return False

            selected_move = self._selected_menu_move(moves, choice)
            if selected_move is not None:
                result = self._resolve_player_move(selected_move)
                if result.accepted:
                    self._complete_accepted_action(
                        self.player_state,
                        (self.foe,),
                        result,
                    )
                    return True
                continue

            print("That is not a valid move. Please try again.")

    def _player_super_menu(self):
        moves = [
            move
            for move in self._player_moves()
            if move.resource_type.value == "super"
        ]

        while True:
            print("\nChoose a Super:")
            for index, move in enumerate(moves, start=1):
                print(
                    f"{index}. {move.name} "
                    f"[{move.resource_type.value} {move.resource_cost}] - "
                    f"{move.description}"
                )
            print("0. Back")

            choice = input("> ").strip().lower()
            if choice == "0":
                return

            selected_move = self._selected_menu_move(moves, choice)
            if selected_move is not None:
                result = self._resolve_player_move(selected_move)
                if result.accepted:
                    self._complete_accepted_action(
                        self.player_state,
                        (self.foe,),
                        result,
                    )
                    return True
                continue

            print("That is not a valid move. Please try again.")

    @staticmethod
    def _selected_menu_move(moves, choice):
        for index, move in enumerate(moves, start=1):
            if choice in (str(index), move.name.lower()):
                return move

        return None

    def enemy_action(self):
        move = random.choice(list(self._enemy_moves()))
        result = self._resolve_enemy_move(move)
        if result.accepted:
            self._complete_accepted_action(
                self.foe,
                (self.player_state,),
                result,
            )

        return result.accepted

    def attack(self, attacker, target, move_name, heavy):
        if self.misses():
            print(f"\n{attacker.display_name} used {move_name}, but missed!")
            return

        if heavy:
            damage = random.randint(8, 20) + attacker.effective_stat("strength")
        else:
            damage = random.randint(8, 14) + attacker.effective_stat("strength")

        target.health.take_damage(damage)
        print(f"\n{attacker.display_name} used {move_name}. It dealt {damage} damage to the {target.display_name}.")

    def heal_player(self):
        heal_amount = random.randint(10, 16) + self.player_state.effective_stat("constitution")
        self.player_state.health.heal(heal_amount)
        print(f"\n{self.player.display_name} takes a breath and recovers {heal_amount} health.")

    @staticmethod
    def misses():
        return random.randint(1, 5) == 1

    def print_health(self):
        print(
            f"\n{self.player.display_name} HP: "
            f"{self.player_state.health.current}/{self.player_state.health.maximum}"
        )
        print(
            f"{self.player.display_name} Mana: "
            f"{self.player_state.mana_resource.current}/{self.player_state.mana_resource.maximum}"
        )
        print(
            f"{self.player.display_name} Super: "
            f"{self.player_state.super_resource.current}/{self.player_state.super_resource.maximum}"
        )
        if self.combat_state.is_defending(self.player_state):
            print(f"{self.player.display_name} Defending: yes")

        print(
            f"{self.foe.display_name} HP: "
            f"{self.foe.health.current}/{self.foe.health.maximum}"
        )
        if self.foe.mana_resource.current or self.foe.mana_resource.maximum:
            print(
                f"{self.foe.display_name} Mana: "
                f"{self.foe.mana_resource.current}/{self.foe.mana_resource.maximum}"
            )
        if self.foe.super_resource.current or self.foe.generates_super:
            print(
                f"{self.foe.display_name} Super: "
                f"{self.foe.super_resource.current}/{self.foe.super_resource.maximum}"
            )
        if self.combat_state.is_defending(self.foe):
            print(f"{self.foe.display_name} Defending: yes")

        if self.combat_state.statuses:
            print(f"Statuses: {self.combat_state.statuses}")
        if self.combat_state.buffs:
            print(f"Buffs: {self.combat_state.buffs}")
        if self.combat_state.debuffs:
            print(f"Debuffs: {self.combat_state.debuffs}")

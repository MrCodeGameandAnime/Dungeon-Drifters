import random
from collections import Counter
from collections.abc import Sequence

from app.combat.combat_state import CombatState
from app.combat.combatant import EnemyCombatant
from app.combat.move import ResourceType, TargetType
from app.combat.resolver import CombatResolver
from app.presentation.battle_models import (
    ActionIntent,
    BattleEventType,
    BattleLogEntry,
    InputRejectionReason,
    InteractionPhase,
)
from app.presentation.battle_presenter import BattlePresenter
from app.presentation.battle_session import BattlePresentationSession
from app.player.inventory_action import InventoryActionResolver
from app.player.run_items import InventoryCommand
from app.ui.battle_ui import (
    ChooseAction,
    ChooseInventoryCommand,
    ChooseInventoryCompanion,
    ChooseInventoryItem,
    ChooseMove,
    ChooseTarget,
    ConfirmInventoryUse,
    GoBack,
)


def select_enemy_move(enemy, rng=random):
    """Choose uniformly from the enemy's currently affordable moves."""
    eligible_moves = tuple(
        move
        for move in enemy.combat_moves
        if move.resource_type is ResourceType.NONE
        or (
            move.resource_type is ResourceType.MANA
            and enemy.mana_resource.can_afford(move.resource_cost)
        )
    )
    if not eligible_moves:
        raise ValueError("enemy has no legal affordable moves")
    return rng.choice(eligible_moves)


class Battle:
    def __init__(
        self,
        player_state,
        enemies,
        ui,
        resolver=None,
        rng=random,
        presenter=None,
        presentation_session=None,
        inventory_action_resolver=None,
    ):
        self.player_state = player_state
        self.player = player_state.character
        self._enemies = self._normalize_enemies(enemies)
        self._enemy_target_ids = tuple(
            f"enemy_{index}" for index in range(1, len(self._enemies) + 1)
        )
        self._enemy_display_labels = self._build_enemy_display_labels(
            self._enemies
        )
        if not callable(getattr(rng, "randint", None)):
            raise TypeError("rng must provide randint")
        if not callable(getattr(rng, "choice", None)):
            raise TypeError("rng must provide choice")
        self.rng = rng
        self.combat_state = CombatState()
        self.resolver = resolver or CombatResolver(rng=self.rng)
        self.ui = ui
        self.presenter = presenter or BattlePresenter()
        self.presentation_session = presentation_session or BattlePresentationSession()
        self.inventory_action_resolver = (
            inventory_action_resolver or InventoryActionResolver()
        )
        self.interaction_phase = InteractionPhase.ACTIONS
        self._selected_inventory_item_id = None
        self._selected_inventory_companion_id = None
        self._selected_move_key = None
        self._originating_move_phase = None

    @staticmethod
    def _normalize_enemies(enemies):
        if isinstance(enemies, EnemyCombatant):
            normalized = (enemies,)
        elif isinstance(enemies, Sequence) and not isinstance(
            enemies,
            (str, bytes, bytearray),
        ):
            normalized = tuple(enemies)
        else:
            raise TypeError(
                "enemies must be an enemy combatant or an ordered enemy sequence"
            )

        if not normalized:
            raise ValueError("Battle requires at least one enemy")
        if len(normalized) > 4:
            raise ValueError("Battle supports at most four enemies")
        if not all(isinstance(enemy, EnemyCombatant) for enemy in normalized):
            raise TypeError("all Battle enemies must be enemy combatants")
        if len({id(enemy) for enemy in normalized}) != len(normalized):
            raise ValueError("the same EnemyState cannot appear more than once")
        return normalized

    @staticmethod
    def _build_enemy_display_labels(enemies):
        counts = Counter(enemy.display_name for enemy in enemies)
        positions = Counter()
        labels = []
        for enemy in enemies:
            name = enemy.display_name
            if counts[name] == 1:
                labels.append(name)
                continue
            positions[name] += 1
            labels.append(f"{name} {positions[name]}")
        return tuple(labels)

    @property
    def enemies(self):
        return self._enemies

    @property
    def foe(self):
        if len(self.enemies) != 1:
            raise ValueError("Battle.foe is available only for single-enemy battles")
        return self.enemies[0]

    @property
    def enemy_target_ids(self):
        return self._enemy_target_ids

    @property
    def enemy_display_labels(self):
        return self._enemy_display_labels

    def _player_moves(self):
        return self.player_state.combat_moves

    def _enemy_moves(self):
        return self.foe.combat_moves

    def _complete_accepted_action(
        self,
        actor,
        opposing_combatants,
        result,
        *,
        reduce_heal_cooldown=True,
        presentation_target=None,
    ):
        if result.accepted:
            if reduce_heal_cooldown:
                outcomes = self.combat_state.complete_accepted_action(
                    actor,
                    opposing_combatants,
                )
            else:
                outcomes = self.combat_state.complete_accepted_action(
                    actor,
                    opposing_combatants,
                    reduce_heal_cooldown=False,
                )
            if outcomes:
                self._record_lifecycle_outcomes(
                    actor,
                    presentation_target,
                    outcomes,
                )
            return outcomes

        return None

    def _record_lifecycle_outcomes(self, actor, target, outcomes):
        self.presentation_session.record(
            BattleLogEntry(
                event_type=BattleEventType.STATUS,
                actor_name=self._display_name_for(actor),
                target_name=(
                    self._display_name_for(target) if target is not None else None
                ),
                outcomes=outcomes,
            )
        )

    def _display_name_for(self, combatant):
        if combatant is self.player_state:
            return self.player_state.display_name
        for enemy, label in zip(
            self.enemies,
            self.enemy_display_labels,
            strict=True,
        ):
            if combatant is enemy:
                return label
        return combatant.display_name

    def _living_enemies(self):
        return tuple(enemy for enemy in self.enemies if enemy.is_alive())

    def _player_target_for_move(self, move):
        if move.target == TargetType.ENEMY:
            living_enemies = self._living_enemies()
            if len(living_enemies) == 1:
                return living_enemies[0]
            if not living_enemies:
                raise ValueError("no living enemy is available")
            raise ValueError("an exact enemy target is required")
        if move.target == TargetType.SELF:
            return self.player_state

        raise ValueError(f"Unsupported player move target: {move.target!r}")

    def _resolve_player_move(self, move, target=None):
        if target is None:
            target = self._player_target_for_move(move)
        result = self.resolver.resolve_move(
            self.player_state,
            target,
            move.name,
            combat_state=self.combat_state,
            character_run_state=self.player_state.character_run_state,
        )
        if result.accepted:
            self.presentation_session.begin_player_turn()
        self._record_move_result(result, actor=self.player_state, target=target)
        return result

    def _enemy_target_for_move(self, move, enemy=None):
        enemy = self.foe if enemy is None else enemy
        if move.target == TargetType.ENEMY:
            return self.player_state
        if move.target == TargetType.SELF:
            return enemy

        raise ValueError(f"Unsupported enemy move target: {move.target!r}")

    def _resolve_enemy_move(self, move, enemy=None):
        enemy = self.foe if enemy is None else enemy
        target = self._enemy_target_for_move(move, enemy)
        result = self.resolver.resolve_move(
            enemy,
            target,
            move.name,
            combat_state=self.combat_state,
        )
        self._record_move_result(result, actor=enemy, target=target)
        return result

    def _record_move_result(self, result, actor, target=None, event_type=None):
        self.presentation_session.record(
            BattleLogEntry(
                event_type=event_type or self._event_type_for_result(result),
                actor_name=self._display_name_for(actor),
                target_name=(
                    self._display_name_for(target) if target is not None else None
                ),
                action_name=result.move_name,
                accepted=result.accepted,
                hit=result.hit,
                amount=result.damage or result.healing,
                critical=result.critical,
                resource_spent=result.resource_spent,
                statuses_applied=result.statuses_applied,
                reason=result.reason,
                outcomes=result.outcomes,
            )
        )

    @staticmethod
    def _event_type_for_result(result):
        if not result.accepted:
            return BattleEventType.ACTION_REJECTED
        if not result.hit:
            return BattleEventType.MISS
        if result.damage:
            return BattleEventType.DAMAGE
        if result.healing:
            return BattleEventType.HEALING
        return BattleEventType.UTILITY

    def _build_view(self):
        return self.presenter.build(
            player=self.player_state,
            enemies=self.enemies,
            enemy_target_ids=self.enemy_target_ids,
            enemy_display_labels=self.enemy_display_labels,
            combat_state=self.combat_state,
            log_entries=self.presentation_session.entries,
            interaction_phase=self.interaction_phase,
            selected_inventory_item_id=self._selected_inventory_item_id,
            selected_inventory_companion_id=self._selected_inventory_companion_id,
            selected_move_key=self._selected_move_key,
            originating_move_phase=self._originating_move_phase,
        )

    def _render_current_view(self):
        view = self._build_view()
        self.ui.render(view)
        return view

    def run(self):
        self.presentation_session.record(
            BattleLogEntry(
                event_type=BattleEventType.ENCOUNTER_START,
                target_name=self._enemy_group_label(),
            )
        )

        player_side_turn = self.rng.randint(1, 2) == 1
        self.presentation_session.record(
            BattleLogEntry(
                event_type=BattleEventType.INITIATIVE,
                actor_name="Player side" if player_side_turn else "Enemy side",
            )
        )

        winner = self._winner()
        while winner is None:
            if player_side_turn and self._skip_action_opportunity_suppression(
                self.player_state
            ):
                player_side_turn = False
                continue

            if player_side_turn:
                self.player_action()
                winner = self._winner()
                if winner is not None:
                    break
            else:
                self.enemy_phase()
                winner = self._winner()
                if winner is not None:
                    break

            player_side_turn = not player_side_turn

        self.presentation_session.record(
            BattleLogEntry(
                event_type=(
                    BattleEventType.VICTORY
                    if winner == "player"
                    else BattleEventType.DEFEAT
                ),
                actor_name=self.player_state.display_name,
                target_name=self._enemy_group_label(),
            )
        )
        self.interaction_phase = InteractionPhase.COMPLETE
        self._clear_inventory_navigation()
        self._clear_move_target_navigation()
        self._render_current_view()
        return winner

    def _enemy_group_label(self):
        return ", ".join(self.enemy_display_labels)

    def _winner(self):
        player_alive = self.player_state.is_alive()
        all_enemies_defeated = all(not enemy.is_alive() for enemy in self.enemies)
        if not player_alive:
            return "enemy"
        if all_enemies_defeated:
            return "player"
        return None

    def _skip_stunned_action_opportunity(self, actor):
        return self._skip_action_opportunity_suppression(actor)

    def _skip_action_opportunity_suppression(self, actor):
        outcomes = self.combat_state.consume_action_opportunity_suppression(actor)
        if not outcomes:
            return False
        opposing_name = (
            self._enemy_group_label()
            if actor is self.player_state
            else self.player_state.display_name
        )
        self.presentation_session.record(
            BattleLogEntry(
                event_type=BattleEventType.STATUS,
                actor_name=self._display_name_for(actor),
                target_name=opposing_name,
                outcomes=outcomes,
            )
        )
        return True

    def player_action(self):
        self.interaction_phase = InteractionPhase.ACTIONS
        self._clear_inventory_navigation()
        self._clear_move_target_navigation()
        while True:
            view = self._render_current_view()
            battle_input = self.ui.read_input(view)
            rejection_reason = self._input_rejection_reason(view, battle_input)
            if rejection_reason is not None:
                self._record_input_rejection(rejection_reason)
                continue

            if isinstance(battle_input, ChooseAction):
                if battle_input.intent == ActionIntent.ATTACK:
                    self._clear_inventory_navigation()
                    self._clear_move_target_navigation()
                    self.interaction_phase = InteractionPhase.REGULAR_MOVES
                    continue
                if battle_input.intent == ActionIntent.HEAL:
                    result = self.resolver.resolve_heal(
                        self.player_state,
                        combat_state=self.combat_state,
                    )
                    if result.accepted:
                        self.presentation_session.begin_player_turn()
                    self._record_move_result(result, actor=self.player_state)
                    if result.accepted:
                        self._complete_accepted_action(
                            self.player_state,
                            self.enemies,
                            result,
                            reduce_heal_cooldown=False,
                        )
                        self.interaction_phase = InteractionPhase.ACTIONS
                        return True
                    continue
                if battle_input.intent == ActionIntent.SUPER:
                    self._clear_inventory_navigation()
                    self._clear_move_target_navigation()
                    self.interaction_phase = InteractionPhase.SUPER_MOVES
                    continue
                if battle_input.intent == ActionIntent.ITEMS:
                    self._clear_inventory_navigation()
                    self.interaction_phase = InteractionPhase.INVENTORY
                    continue
                if battle_input.intent == ActionIntent.DEFEND:
                    result = self.resolver.resolve_defend(
                        self.player_state,
                        self.combat_state,
                    )
                    if result.accepted:
                        self.presentation_session.begin_player_turn()
                    self._record_move_result(
                        result,
                        actor=self.player_state,
                        event_type=(
                            BattleEventType.DEFEND
                            if result.accepted
                            else BattleEventType.ACTION_REJECTED
                        ),
                    )
                    if result.accepted:
                        self._complete_accepted_action(
                            self.player_state,
                            self.enemies,
                            result,
                        )
                        self.interaction_phase = InteractionPhase.ACTIONS
                        return True
                    continue

            if isinstance(battle_input, GoBack):
                self._navigate_back()
                continue

            if isinstance(battle_input, ChooseInventoryItem):
                self._selected_inventory_item_id = battle_input.item_id
                self._selected_inventory_companion_id = None
                self.interaction_phase = InteractionPhase.INVENTORY_ITEM
                continue

            if isinstance(battle_input, ChooseInventoryCommand):
                self._selected_inventory_companion_id = None
                if battle_input.command == InventoryCommand.INSPECT:
                    self.interaction_phase = InteractionPhase.INVENTORY_INSPECT
                else:
                    self.interaction_phase = InteractionPhase.INVENTORY_COMBINATION
                continue

            if isinstance(battle_input, ChooseInventoryCompanion):
                self._selected_inventory_companion_id = battle_input.item_id
                self.interaction_phase = InteractionPhase.INVENTORY_CONFIRMATION
                continue

            if isinstance(battle_input, ConfirmInventoryUse):
                if not battle_input.confirmed:
                    self._selected_inventory_companion_id = None
                    self.interaction_phase = InteractionPhase.INVENTORY_ITEM
                    continue
                confirmation = view.inventory_confirmation
                result = self.inventory_action_resolver.resolve(
                    confirmation.action_id,
                    self.player_state.character_run_state,
                )
                if result.accepted:
                    self.presentation_session.begin_player_turn()
                self._record_inventory_action_result(result)
                if result.accepted:
                    self._complete_accepted_action(
                        self.player_state,
                        self.enemies,
                        result,
                    )
                    self.interaction_phase = InteractionPhase.ACTIONS
                    self._clear_inventory_navigation()
                    return True
                continue

            if isinstance(battle_input, ChooseMove):
                move = self._move_for_key(view, battle_input.move_key)
                if move.target == TargetType.ENEMY and len(self._living_enemies()) > 1:
                    self._selected_move_key = move.name
                    self._originating_move_phase = self.interaction_phase
                    self.interaction_phase = InteractionPhase.TARGETS
                    continue

                target = self._player_target_for_move(move)
                result = self._resolve_player_move(move, target)
                if result.accepted:
                    self._complete_accepted_action(
                        self.player_state,
                        self.enemies,
                        result,
                        presentation_target=(
                            target if move.target == TargetType.ENEMY else None
                        ),
                    )
                    self.interaction_phase = InteractionPhase.ACTIONS
                    self._clear_inventory_navigation()
                    self._clear_move_target_navigation()
                    return True

            if isinstance(battle_input, ChooseTarget):
                move = self._pending_move()
                target = self._enemy_for_target_id(battle_input.target_id)
                result = self._resolve_player_move(move, target)
                if result.accepted:
                    self._complete_accepted_action(
                        self.player_state,
                        self.enemies,
                        result,
                        presentation_target=target,
                    )
                    self.interaction_phase = InteractionPhase.ACTIONS
                    self._clear_inventory_navigation()
                    self._clear_move_target_navigation()
                    return True

    def _navigate_back(self):
        if self.interaction_phase == InteractionPhase.TARGETS:
            self.interaction_phase = self._originating_move_phase
            self._clear_move_target_navigation()
            return
        if self.interaction_phase == InteractionPhase.INVENTORY_ITEM:
            self.interaction_phase = InteractionPhase.INVENTORY
            self._clear_inventory_navigation()
            return
        if self.interaction_phase in {
            InteractionPhase.INVENTORY_INSPECT,
            InteractionPhase.INVENTORY_COMBINATION,
        }:
            self.interaction_phase = InteractionPhase.INVENTORY_ITEM
            self._selected_inventory_companion_id = None
            return
        if self.interaction_phase == InteractionPhase.INVENTORY_CONFIRMATION:
            self.interaction_phase = InteractionPhase.INVENTORY_COMBINATION
            self._selected_inventory_companion_id = None
            return
        self.interaction_phase = InteractionPhase.ACTIONS
        self._clear_inventory_navigation()
        self._clear_move_target_navigation()

    def _clear_inventory_navigation(self):
        self._selected_inventory_item_id = None
        self._selected_inventory_companion_id = None

    def _clear_move_target_navigation(self):
        self._selected_move_key = None
        self._originating_move_phase = None

    def _enemy_for_target_id(self, target_id):
        for current_id, enemy in zip(
            self.enemy_target_ids,
            self.enemies,
            strict=True,
        ):
            if current_id == target_id:
                return enemy
        raise ValueError("target ID does not belong to this Battle")

    def _pending_move(self):
        if self.interaction_phase != InteractionPhase.TARGETS:
            raise ValueError("Battle is not selecting a target")
        if self._selected_move_key is None or self._originating_move_phase is None:
            raise ValueError("no authored move is pending")
        for move in self._player_moves():
            if move.name == self._selected_move_key:
                return move
        raise ValueError("pending authored move is unavailable")

    def _target_rejection_reason(self, target_id):
        if self.interaction_phase != InteractionPhase.TARGETS:
            return InputRejectionReason.TARGET_UNAVAILABLE
        try:
            move = self._pending_move()
            target = self._enemy_for_target_id(target_id)
        except ValueError:
            return InputRejectionReason.TARGET_UNAVAILABLE
        if move.target != TargetType.ENEMY or not target.is_alive():
            return InputRejectionReason.TARGET_UNAVAILABLE

        origin_view = self.presenter.build(
            player=self.player_state,
            enemies=self.enemies,
            enemy_target_ids=self.enemy_target_ids,
            enemy_display_labels=self.enemy_display_labels,
            combat_state=self.combat_state,
            interaction_phase=self._originating_move_phase,
        )
        if not any(
            option.selection_key == self._selected_move_key and option.enabled
            for option in origin_view.move_options
        ):
            return InputRejectionReason.TARGET_UNAVAILABLE

        current_view = self._build_view()
        if not any(
            option.target_id == target_id and option.enabled
            for option in current_view.target_options
        ):
            return InputRejectionReason.TARGET_UNAVAILABLE
        return None

    def _move_for_key(self, view, move_key):
        for option in view.move_options:
            if option.selection_key == move_key:
                for move in self._player_moves():
                    if move.name == option.selection_key:
                        return move
        raise ValueError("move key was not offered")

    def _record_inventory_action_result(self, result):
        self.presentation_session.record(
            BattleLogEntry(
                event_type=BattleEventType.INVENTORY,
                actor_name=self.player_state.display_name,
                action_name=result.action_id.value,
                accepted=result.accepted,
                reason=result.reason.value if result.reason is not None else None,
                outcomes=result.outcomes,
            )
        )

    def _input_rejection_reason(self, view, battle_input):
        if isinstance(battle_input, ChooseAction):
            if battle_input.intent == ActionIntent.SUPER:
                if view.super_meter.activation_offered:
                    return None
                return InputRejectionReason.SUPER_UNAVAILABLE
            if view.interaction_phase != InteractionPhase.ACTIONS:
                return InputRejectionReason.ACTION_UNAVAILABLE
            if any(
                option.intent == battle_input.intent and option.enabled
                for option in view.action_options
            ):
                return None
            return InputRejectionReason.ACTION_UNAVAILABLE

        if isinstance(battle_input, ChooseMove):
            if view.interaction_phase == InteractionPhase.ACTIONS:
                return InputRejectionReason.MOVE_UNAVAILABLE
            if any(
                option.selection_key == battle_input.move_key and option.enabled
                for option in view.move_options
            ):
                return None
            return InputRejectionReason.MOVE_UNAVAILABLE

        if isinstance(battle_input, ChooseTarget):
            return self._target_rejection_reason(battle_input.target_id)

        if isinstance(battle_input, ChooseInventoryItem):
            if view.interaction_phase != InteractionPhase.INVENTORY:
                return InputRejectionReason.INVENTORY_ITEM_UNAVAILABLE
            if any(
                option.item_id == battle_input.item_id and option.enabled
                for option in view.inventory_items
            ):
                return None
            return InputRejectionReason.INVENTORY_ITEM_UNAVAILABLE

        if isinstance(battle_input, ChooseInventoryCommand):
            if view.interaction_phase != InteractionPhase.INVENTORY_ITEM:
                return InputRejectionReason.INVENTORY_COMMAND_UNAVAILABLE
            if any(
                option.command == battle_input.command and option.enabled
                for option in view.inventory_commands
            ):
                return None
            return InputRejectionReason.INVENTORY_COMMAND_UNAVAILABLE

        if isinstance(battle_input, ChooseInventoryCompanion):
            if view.interaction_phase != InteractionPhase.INVENTORY_COMBINATION:
                return InputRejectionReason.INVENTORY_COMPANION_UNAVAILABLE
            if any(
                option.item_id == battle_input.item_id and option.enabled
                for option in view.inventory_companions
            ):
                return None
            return InputRejectionReason.INVENTORY_COMPANION_UNAVAILABLE

        if isinstance(battle_input, ConfirmInventoryUse):
            if (
                view.interaction_phase == InteractionPhase.INVENTORY_CONFIRMATION
                and view.inventory_confirmation is not None
            ):
                return None
            return InputRejectionReason.INVENTORY_CONFIRMATION_UNAVAILABLE

        if isinstance(battle_input, GoBack):
            if view.interaction_phase != InteractionPhase.ACTIONS:
                return None
            return InputRejectionReason.BACK_UNAVAILABLE

        return InputRejectionReason.ACTION_UNAVAILABLE

    def _record_input_rejection(self, reason):
        entry = BattleLogEntry(
            event_type=BattleEventType.INPUT_REJECTED,
            rejection_reason=reason,
        )
        if reason == InputRejectionReason.TARGET_UNAVAILABLE:
            self.presentation_session.record_transient_rejection(entry)
            return
        self.presentation_session.record(entry)

    def enemy_phase(self):
        for enemy in self.enemies:
            if self._winner() is not None:
                return
            if not enemy.is_alive():
                continue
            if self._skip_action_opportunity_suppression(enemy):
                continue
            self.enemy_action(enemy)
            if self._winner() is not None:
                return

    def enemy_action(self, enemy=None):
        enemy = self.foe if enemy is None else enemy
        if not any(current is enemy for current in self.enemies):
            raise ValueError("enemy does not belong to this Battle")
        if not enemy.is_alive():
            raise ValueError("defeated enemies cannot act")

        move = select_enemy_move(enemy, self.rng)
        result = self._resolve_enemy_move(move, enemy)
        if not result.accepted:
            raise RuntimeError("enemy resolver rejected a legal selected move")

        self._complete_accepted_action(
            enemy,
            (self.player_state,),
            result,
            presentation_target=self.player_state,
        )
        return True

import app.randomness as random
from collections.abc import Sequence

from app.combat.combat_state import CombatState
from app.combat.combatant import is_enemy_combatant
from app.combat.move import ResourceType, TargetType
from app.combat.resolver import CombatResolver
from app.combat.result import MoveResult
from app.presentation.battle_models import (
    ActionIntent,
    BattleEventType,
    BattleLogEntry,
    BattleView,
    InputRejectionReason,
    InteractionPhase,
)
from app.presentation.battle_presenter import BattlePresenter
from app.presentation.battle_session import BattlePresentationSession
from app.player.inventory_action import InventoryActionResolver
from app.player.player_state import PlayerState
from app.player.run_items import InventoryCommand
from app.ui.battle_ui import (
    BattleInput,
    ChooseAction,
    ChooseInventoryCommand,
    ChooseInventoryCompanion,
    ChooseInventoryItem,
    ChooseHealingTarget,
    ChooseMove,
    ChooseTarget,
    ConfirmInventoryUse,
    GoBack,
)


_MISSING_UI = object()


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
        ui=_MISSING_UI,
        resolver=None,
        rng=random,
        encounter_label=None,
        presenter=None,
        presentation_session=None,
        inventory_action_resolver=None,
        party=(),
        party_state=None,
        smoke_escape_allowed=False,
    ):
        if not isinstance(player_state, PlayerState):
            raise TypeError("player_state must be a PlayerState")
        self.player_state = player_state
        if not isinstance(party, Sequence) or isinstance(
            party,
            (str, bytes, bytearray),
        ):
            raise TypeError("party must be an ordered player-state sequence")
        if party:
            party_members = (player_state,) + tuple(party)
            if not all(isinstance(member, PlayerState) for member in party_members):
                raise TypeError("party must contain PlayerState values")
            drifter_ids = tuple(self._drifter_id(member) for member in party_members)
            if len(set(drifter_ids)) != len(drifter_ids):
                raise ValueError("party Drifter IDs must be unique")
            self._party_members = party_members
            self._party_turn_queue = []
            self._party_dexterity_snapshot = {}
        if party_state is not None and not callable(
            getattr(party_state, "consume_carried_supplies", None)
        ):
            raise TypeError("party_state must provide carried-supply operations")
        if not isinstance(smoke_escape_allowed, bool):
            raise TypeError("smoke_escape_allowed must be a boolean")
        self._party_state = party_state
        self._smoke_escape_allowed = smoke_escape_allowed
        self.player = player_state.character
        self._enemies = self._normalize_enemies(enemies)
        self._enemy_target_ids = tuple(
            f"enemy_{index}" for index in range(1, len(self._enemies) + 1)
        )
        self._enemy_display_labels = self._build_enemy_display_labels(
            self._enemies
        )
        self.encounter_label = encounter_label or self._enemy_group_label()
        if not callable(getattr(rng, "randint", None)):
            raise TypeError("rng must provide randint")
        if not callable(getattr(rng, "choice", None)):
            raise TypeError("rng must provide choice")
        self.rng = rng
        self.combat_state = CombatState()
        self.resolver = resolver or CombatResolver(rng=self.rng)
        self._step_driven = ui is None
        self.ui = None if ui is _MISSING_UI else ui
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
        self._started = False
        self._player_side_turn = None
        self._winner_result = None
        self._final_view = None
        if self._step_driven:
            self._ensure_started()

    @staticmethod
    def _normalize_enemies(enemies):
        if is_enemy_combatant(enemies):
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
        if not all(is_enemy_combatant(enemy) for enemy in normalized):
            raise TypeError("all Battle enemies must be enemy combatants")
        if len({id(enemy) for enemy in normalized}) != len(normalized):
            raise ValueError("the same EnemyState cannot appear more than once")
        return normalized

    @staticmethod
    def _build_enemy_display_labels(enemies):
        counts = {}
        for enemy in enemies:
            name = enemy.display_name
            counts[name] = counts.get(name, 0) + 1

        positions = {}
        labels = []
        for enemy in enemies:
            name = enemy.display_name
            if counts[name] == 1:
                labels.append(name)
                continue
            position = positions.get(name, 0) + 1
            positions[name] = position
            labels.append(f"{name} {position}")
        return tuple(labels)

    @property
    def enemies(self):
        return self._enemies

    @property
    def active_player_id(self):
        if not self._party_mode:
            return None
        return self._drifter_id(self.player_state)

    @property
    def party(self):
        return self.party_states

    @property
    def party_states(self):
        party_members = getattr(self, "_party_members", None)
        return party_members if party_members is not None else (self.player_state,)

    @property
    def _party_mode(self):
        return getattr(self, "_party_members", None) is not None

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

    @property
    def is_complete(self):
        return self._winner_result is not None

    @property
    def winner(self):
        return self._winner_result

    def current_view(self) -> BattleView:
        self._ensure_started()
        if self._final_view is not None:
            return self._final_view
        return self._build_view()

    def submit(self, battle_input: BattleInput) -> BattleView:
        self._ensure_started()
        if self.is_complete:
            return self._final_view

        view = self._build_view()
        rejection_reason = self._input_rejection_reason(view, battle_input)
        if rejection_reason is not None:
            self._record_input_rejection(rejection_reason)
            return self._build_view()

        accepted_action = self._process_player_input(view, battle_input)
        if accepted_action:
            if self.is_complete:
                return self._final_view
            if self._party_mode:
                acting_player = self.player_state
                winner = self._winner()
                if winner is not None:
                    return self._finish(winner)
                self._consume_party_turn(acting_player)
                self._advance_automatic_state()
                if self._final_view is not None:
                    return self._final_view
                return self._build_view()
            winner = self._winner()
            if winner is not None:
                return self._finish(winner)
            self._player_side_turn = False
            self._advance_automatic_state()

        if self._final_view is not None:
            return self._final_view
        return self._build_view()

    def _ensure_started(self):
        if self._started:
            return
        self._started = True
        self.presentation_session.record(
            BattleLogEntry(
                event_type=BattleEventType.ENCOUNTER_START,
                target_name=self._enemy_group_label(),
            )
        )

        if self._party_mode:
            self._start_party_round()
        else:
            self._player_side_turn = self.rng.randint(1, 2) == 1
            self.presentation_session.record(
                BattleLogEntry(
                    event_type=BattleEventType.INITIATIVE,
                    actor_name=(
                        "Player side" if self._player_side_turn else "Enemy side"
                    ),
                )
            )
        self._advance_automatic_state()

    def _advance_automatic_state(self):
        if self._party_mode:
            self._advance_party_state()
            return
        while not self.is_complete:
            if self._player_side_turn:
                if self._skip_action_opportunity_suppression(self.player_state):
                    self._player_side_turn = False
                    continue
                return

            self._advance_enemy_phase()
            winner = self._winner()
            if winner is not None:
                self._finish(winner)
                return
            self._player_side_turn = True

    def _advance_party_state(self):
        while not self.is_complete:
            winner = self._winner()
            if winner is not None:
                self._finish(winner)
                return
            if not self._party_turn_queue:
                self._start_party_round()
                if not self._party_turn_queue:
                    self._finish("enemy")
                    return

            actor = self._party_turn_queue[0]
            if not actor.is_alive():
                self._consume_party_turn(actor)
                continue
            if self._is_party_member(actor):
                self._activate_party_member(actor)
                if self._skip_action_opportunity_suppression(actor):
                    self._consume_party_turn(actor)
                    continue
                return
            if self._skip_action_opportunity_suppression(actor):
                self._consume_party_turn(actor)
                continue
            self._process_enemy_action(actor)
            winner = self._winner()
            if winner is not None:
                self._finish(winner)
                return
            self._consume_party_turn(actor)

    def _start_party_round(self):
        combatants = tuple(
            actor
            for actor in self._party_members + self.enemies
            if actor.is_alive()
        )
        self._party_turn_queue = self._ordered_by_dexterity(combatants)
        self._party_dexterity_snapshot = {
            id(actor): self._effective_dexterity(actor)
            for actor in self._party_members + self.enemies
        }
        if self._party_turn_queue:
            self.presentation_session.record(
                BattleLogEntry(
                    event_type=BattleEventType.INITIATIVE,
                    actor_name=" -> ".join(
                        self._display_name_for(actor)
                        for actor in self._party_turn_queue
                    ),
                )
            )

    def _ordered_by_dexterity(self, combatants):
        groups = {}
        for actor in combatants:
            groups.setdefault(self._effective_dexterity(actor), []).append(actor)
        ordered = []
        for dexterity in sorted(groups, reverse=True):
            tied = groups[dexterity]
            while tied:
                actor = self.rng.choice(tuple(tied))
                tied.remove(actor)
                ordered.append(actor)
        return ordered

    def _consume_party_turn(self, actor):
        if self._party_turn_queue and self._party_turn_queue[0] is actor:
            self._party_turn_queue.pop(0)
        else:
            self._party_turn_queue = [
                current for current in self._party_turn_queue if current is not actor
            ]

        current_snapshot = {
            id(combatant): self._effective_dexterity(combatant)
            for combatant in self._party_members + self.enemies
        }
        remaining = tuple(
            combatant
            for combatant in self._party_turn_queue
            if combatant.is_alive()
        )
        dexterity_changed = any(
            self._party_dexterity_snapshot.get(id(combatant))
            != current_snapshot[id(combatant)]
            for combatant in remaining
        )
        if dexterity_changed:
            self._party_turn_queue = self._ordered_by_dexterity(remaining)
        self._party_dexterity_snapshot = current_snapshot

    def _activate_party_member(self, player_state):
        self.player_state = player_state
        self.player = player_state.character

    def _is_party_member(self, combatant):
        if not self._party_mode:
            return combatant is self.player_state
        return any(member is combatant for member in self._party_members)

    @staticmethod
    def _effective_dexterity(combatant):
        return combatant.effective_stat("dexterity")

    @staticmethod
    def _drifter_id(player_state):
        profile = getattr(player_state.character, "profile", None)
        if profile is None:
            raise ValueError("party members require canonical Drifter profiles")
        from app.content.catalog import get_drifter_spec

        try:
            canonical_profile = get_drifter_spec(profile.drifter_id)
        except (AttributeError, ValueError) as error:
            raise ValueError(
                "party members require canonical Drifter profiles"
            ) from error
        if profile is not canonical_profile:
            raise ValueError("party members require canonical Drifter profiles")
        return canonical_profile.drifter_id

    def _finish(self, winner):
        if self.is_complete:
            return self._final_view
        self._winner_result = winner
        self.presentation_session.record(
            BattleLogEntry(
                event_type=(
                    BattleEventType.VICTORY
                    if winner == "player"
                    else BattleEventType.DEFEAT
                ),
                actor_name=(
                    self._party_members[0].display_name
                    if self._party_mode
                    else self.player_state.display_name
                ),
                target_name=self._enemy_group_label(),
            )
        )
        self.interaction_phase = InteractionPhase.COMPLETE
        self._clear_inventory_navigation()
        self._clear_move_target_navigation()
        self._final_view = self._build_view()
        return self._final_view

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
        if self._party_mode:
            for member in self._party_members:
                if combatant is member:
                    return member.display_name
        elif combatant is self.player_state:
            return self.player_state.display_name
        for enemy, label in zip(
            self.enemies,
            self.enemy_display_labels,
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

    def _enemy_target_for_move(self, move, enemy=None, target=None):
        enemy = self.foe if enemy is None else enemy
        if move.target == TargetType.ENEMY:
            if target is not None:
                if self._party_mode:
                    valid_target = any(
                        target is member for member in self._party_members
                    )
                else:
                    valid_target = target is self.player_state
                if not valid_target:
                    raise ValueError("enemy target does not belong to this party")
                if not target.is_alive():
                    raise ValueError("defeated Drifters cannot be targeted")
                return target
            if self._party_mode:
                living_party = tuple(
                    member for member in self._party_members if member.is_alive()
                )
                if not living_party:
                    raise ValueError("no living Drifter is available")
                return self.rng.choice(living_party)
            return self.player_state
        if move.target == TargetType.SELF:
            return enemy

        raise ValueError(f"Unsupported enemy move target: {move.target!r}")

    def _resolve_enemy_move(self, move, enemy=None, target=None):
        enemy = self.foe if enemy is None else enemy
        target = self._enemy_target_for_move(move, enemy, target)
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
            encounter_label=self.encounter_label,
            enemy_target_ids=self.enemy_target_ids,
            enemy_display_labels=self.enemy_display_labels,
            combat_state=self.combat_state,
            log_entries=self.presentation_session.entries,
            interaction_phase=self.interaction_phase,
            selected_inventory_item_id=self._selected_inventory_item_id,
            selected_inventory_companion_id=self._selected_inventory_companion_id,
            selected_move_key=self._selected_move_key,
            originating_move_phase=self._originating_move_phase,
            party=(self._party_members if self._party_mode else None),
            active_player_id=(self.active_player_id if self._party_mode else None),
            carried_items=(
                self._party_state.carried_items
                if self._party_state is not None
                else None
            ),
            smoke_escape_allowed=self._smoke_escape_allowed,
        )

    def _render_current_view(self):
        if self.ui is None:
            raise RuntimeError("Battle UI is required by compatibility drivers")
        view = self._build_view()
        self.ui.render(view)
        return view

    def run(self):
        if self.ui is None:
            raise RuntimeError("Battle UI is required by Battle.run()")
        if "player_action" in self.__dict__ or "enemy_action" in self.__dict__:
            return self._run_with_compatibility_overrides()
        view = self.current_view()
        while True:
            self.ui.render(view)
            if self.is_complete:
                return self.winner
            view = self.submit(self.ui.read_input(view))

    def _run_with_compatibility_overrides(self):
        self._ensure_started()
        while not self.is_complete:
            if self._player_side_turn:
                if self._skip_action_opportunity_suppression(self.player_state):
                    self._player_side_turn = False
                    continue
                self.player_action()
                winner = self._winner()
                if winner is not None:
                    self._finish(winner)
                    break
                self._player_side_turn = False
                continue

            self._advance_enemy_phase()
            winner = self._winner()
            if winner is not None:
                self._finish(winner)
                break
            self._player_side_turn = True

        self.ui.render(self._final_view)
        return self.winner

    def _enemy_group_label(self):
        return ", ".join(self.enemy_display_labels)

    def _winner(self):
        if self._party_mode:
            party_alive = any(member.is_alive() for member in self._party_members)
            all_enemies_defeated = all(not enemy.is_alive() for enemy in self.enemies)
            if not party_alive:
                return "enemy"
            if all_enemies_defeated:
                return "player"
            return None
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
            if self._is_party_member(actor)
            else (
                " and ".join(
                    member.display_name for member in self._party_members
                )
                if self._party_mode
                else self.player_state.display_name
            )
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
        if self.ui is None:
            raise RuntimeError("Battle UI is required by Battle.player_action()")
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

            if self._process_player_input(view, battle_input):
                return True

    def _process_player_input(self, view, battle_input):
        if isinstance(battle_input, ChooseAction):
            if battle_input.intent == ActionIntent.ATTACK:
                self._clear_inventory_navigation()
                self._clear_move_target_navigation()
                self.interaction_phase = InteractionPhase.REGULAR_MOVES
                return False
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
                return False
            if battle_input.intent == ActionIntent.SUPER:
                self._clear_inventory_navigation()
                self._clear_move_target_navigation()
                self.interaction_phase = InteractionPhase.SUPER_MOVES
                return False
            if battle_input.intent == ActionIntent.ITEMS:
                self._clear_inventory_navigation()
                self.interaction_phase = InteractionPhase.INVENTORY
                return False
            if battle_input.intent == ActionIntent.HEALING_POTION:
                self.interaction_phase = InteractionPhase.HEALING_TARGETS
                return False
            if battle_input.intent == ActionIntent.ESCAPE:
                if (
                    not self._smoke_escape_allowed
                    or self._party_state is None
                    or not self._party_state.consume_carried_supplies(
                        {"smoke_bomb": 1}
                    )
                ):
                    return False
                self.presentation_session.record(
                    BattleLogEntry(
                        event_type=BattleEventType.ESCAPE,
                        actor_name=self.player_state.display_name,
                        action_name="Smoke Bomb",
                        accepted=True,
                    )
                )
                self._winner_result = "escaped"
                self.interaction_phase = InteractionPhase.COMPLETE
                self._clear_inventory_navigation()
                self._clear_move_target_navigation()
                self._final_view = self._build_view()
                return True
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
                return False

        if isinstance(battle_input, GoBack):
            self._navigate_back()
            return False

        if isinstance(battle_input, ChooseInventoryItem):
            self._selected_inventory_item_id = battle_input.item_id
            self._selected_inventory_companion_id = None
            self.interaction_phase = InteractionPhase.INVENTORY_ITEM
            return False

        if isinstance(battle_input, ChooseInventoryCommand):
            self._selected_inventory_companion_id = None
            if battle_input.command == InventoryCommand.INSPECT:
                self.interaction_phase = InteractionPhase.INVENTORY_INSPECT
            else:
                self.interaction_phase = InteractionPhase.INVENTORY_COMBINATION
            return False

        if isinstance(battle_input, ChooseInventoryCompanion):
            self._selected_inventory_companion_id = battle_input.item_id
            self.interaction_phase = InteractionPhase.INVENTORY_CONFIRMATION
            return False

        if isinstance(battle_input, ConfirmInventoryUse):
            if not battle_input.confirmed:
                self._selected_inventory_companion_id = None
                self.interaction_phase = InteractionPhase.INVENTORY_ITEM
                return False
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
            return False

        if isinstance(battle_input, ChooseMove):
            move = self._move_for_key(view, battle_input.move_key)
            if move.target == TargetType.ENEMY and len(self._living_enemies()) > 1:
                self._selected_move_key = move.name
                self._originating_move_phase = self.interaction_phase
                self.interaction_phase = InteractionPhase.TARGETS
                return False

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

            return False

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

            return False

        if isinstance(battle_input, ChooseHealingTarget):
            target = None
            for member in self.party_states:
                if f"drifter_{self._drifter_id(member)}" == battle_input.target_id:
                    target = member
                    break
            if (
                target is None
                or self._party_state is None
            ):
                return False
            before_healing = target.health.current
            if not self._party_state.use_healing_potion(
                target,
                deployed_members=tuple(self.party_states),
            ):
                return False
            healing = target.health.current
            item = MoveResult(
                accepted=True,
                hit=True,
                move_name="Healing Potion",
                resource_spent=0,
                damage=0,
                healing=healing - before_healing,
                statuses_applied=(),
                reason=None,
            )
            self.presentation_session.begin_player_turn()
            self._record_move_result(
                item,
                actor=self.player_state,
                target=target,
                event_type=BattleEventType.HEALING,
            )
            self._complete_accepted_action(
                self.player_state,
                self.enemies,
                item,
                presentation_target=target,
            )
            self.interaction_phase = InteractionPhase.ACTIONS
            return True

        return False

    def _navigate_back(self):
        if self.interaction_phase == InteractionPhase.TARGETS:
            self.interaction_phase = self._originating_move_phase
            self._clear_move_target_navigation()
            return
        if self.interaction_phase == InteractionPhase.HEALING_TARGETS:
            self.interaction_phase = InteractionPhase.ACTIONS
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

        if isinstance(battle_input, ChooseHealingTarget):
            if view.interaction_phase != InteractionPhase.HEALING_TARGETS:
                return InputRejectionReason.TARGET_UNAVAILABLE
            return (
                None
                if any(
                    option.target_id == battle_input.target_id
                    for option in view.healing_target_options
                )
                else InputRejectionReason.TARGET_UNAVAILABLE
            )

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

    def _advance_enemy_phase(self):
        for enemy in self.enemies:
            if self._winner() is not None:
                return
            if not enemy.is_alive():
                continue
            if self._skip_action_opportunity_suppression(enemy):
                continue
            self._process_enemy_action(enemy)
            if self._winner() is not None:
                return

    def enemy_phase(self):
        return self._advance_enemy_phase()

    def _process_enemy_action(self, enemy):
        enemy = self.foe if enemy is None else enemy
        if not any(current is enemy for current in self.enemies):
            raise ValueError("enemy does not belong to this Battle")
        if not enemy.is_alive():
            raise ValueError("defeated enemies cannot act")

        move = select_enemy_move(enemy, self.rng)
        target = self._enemy_target_for_move(move, enemy)
        result = self._resolve_enemy_move(move, enemy, target)
        if not result.accepted:
            raise RuntimeError("enemy resolver rejected a legal selected move")

        self._complete_accepted_action(
            enemy,
            self._party_members if self._party_mode else (self.player_state,),
            result,
            presentation_target=target,
        )
        return True

    def enemy_action(self, enemy=None):
        enemy = self.foe if enemy is None else enemy
        return self._process_enemy_action(enemy)

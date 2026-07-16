import app.combat.battle as battle_module
from app.combat.battle import Battle
from app.combat.combat_state import CombatState
from app.combat.resolver import CombatResolver
from app.combat.result import CombatOutcomeType
from app.enemies.goblin.definition import Goblin
from app.enemies.state import EnemyState
from app.player.character import BlackMage, Brawler, Monk, RogueArcher
from app.player.character_run_state import PreparedPayloadId, RunItemId
from app.player.inventory_action import (
    InventoryActionRejectionReason,
    InventoryActionResolver,
)
from app.player.player_state import PlayerState
from app.player.run_items import InventoryCommand
from app.presentation.battle_models import ActionIntent, BattleEventType, InteractionPhase
from app.presentation.battle_session import BattlePresentationSession
from app.ui.battle_ui import (
    ChooseAction,
    ChooseInventoryCommand,
    ChooseInventoryCompanion,
    ChooseInventoryItem,
    ChooseMove,
    ConfirmInventoryUse,
)


class AlwaysOneRng:
    @staticmethod
    def randint(_start, _end):
        return 1


class ScriptedRng:
    def __init__(self, *rolls):
        self.rolls = list(rolls)

    def randint(self, _start, _end):
        if not self.rolls:
            raise AssertionError("unexpected random roll")
        return self.rolls.pop(0)


class RecordingPresentationSession(BattlePresentationSession):
    def __init__(self):
        super().__init__()
        self.history = []

    def record(self, entry):
        self.history.append(entry)
        super().record(entry)


class ZhaivraLoopUI:
    def __init__(self, *, first_item="ember_shard", companion="deep_coal"):
        self.stage = "stock"
        self.rendered_views = []
        self.inputs = []
        self.defend_count = 0
        self.first_item = first_item
        self.companion = companion

    def render(self, view):
        self.rendered_views.append(view)

    def read_input(self, view):
        if len(self.inputs) >= 100:
            raise AssertionError("Zhaivra vertical slice did not terminate")

        if view.interaction_phase == InteractionPhase.ACTIONS:
            if self.stage == "stock":
                battle_input = ChooseAction(ActionIntent.ITEMS)
            elif self.stage == "fire":
                battle_input = ChooseAction(ActionIntent.ATTACK)
            elif self.stage == "hold" and any(
                label in view.enemy.temporary_labels
                for label in ("Burn", "Poison")
            ):
                self.defend_count += 1
                battle_input = ChooseAction(ActionIntent.DEFEND)
            else:
                self.stage = "finish"
                battle_input = ChooseAction(ActionIntent.ATTACK)
        elif view.interaction_phase == InteractionPhase.INVENTORY:
            battle_input = ChooseInventoryItem(self.first_item)
        elif view.interaction_phase == InteractionPhase.INVENTORY_ITEM:
            battle_input = ChooseInventoryCommand(InventoryCommand.USE)
        elif view.interaction_phase == InteractionPhase.INVENTORY_COMBINATION:
            battle_input = ChooseInventoryCompanion(self.companion)
        elif view.interaction_phase == InteractionPhase.INVENTORY_CONFIRMATION:
            self.stage = "fire"
            battle_input = ConfirmInventoryUse(True)
        elif view.interaction_phase == InteractionPhase.REGULAR_MOVES:
            if self.stage == "fire":
                self.stage = "hold"
                selection_key = "Infused Barb"
            else:
                selection_key = "Mournpoint Verdict"
            battle_input = ChooseMove(selection_key)
        else:
            raise AssertionError(f"unexpected interaction phase: {view.interaction_phase}")

        self.inputs.append(battle_input)
        return battle_input


class UnusedUI:
    def render(self, view):
        raise AssertionError("rendering is not expected")

    def read_input(self, view):
        raise AssertionError("input is not expected")


def _outcomes(entries):
    return tuple(
        outcome
        for entry in entries
        for outcome in entry.outcomes
    )


def test_complete_stock_prepare_loose_burn_goblin_vertical_slice(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda _start, _end: 1)
    monkeypatch.setattr(battle_module.random, "choice", lambda moves: moves[0])
    player = PlayerState(RogueArcher())
    enemy = EnemyState(Goblin())
    ui = ZhaivraLoopUI()
    session = RecordingPresentationSession()
    battle = Battle(
        player,
        enemy,
        ui=ui,
        resolver=CombatResolver(rng=AlwaysOneRng()),
        presentation_session=session,
    )

    winner = battle.run()

    assert winner == "player"
    assert enemy.health.current == 0
    assert player.character_run_state.item_quantity(RunItemId.EMBER_SHARD) == 0
    assert player.character_run_state.item_quantity(RunItemId.DEEP_COAL) == 0
    assert player.character_run_state.item_quantity(RunItemId.NIGHT_BERRY) == 1
    assert player.character_run_state.payload_prepared(
        PreparedPayloadId.CINDERWRIT
    ) is False
    assert battle.combat_state.burn_active(enemy) is False
    assert ui.defend_count == 2

    outcomes = _outcomes(session.history)
    outcome_types = tuple(outcome.outcome_type for outcome in outcomes)
    assert outcome_types.count(CombatOutcomeType.COMPOUNDS_CONSUMED) == 1
    assert outcome_types.count(CombatOutcomeType.FIRE_INFUSION_PREPARED) == 1
    assert outcome_types.count(CombatOutcomeType.INFUSED_BARB_CONSUMED) == 1
    assert outcome_types.count(CombatOutcomeType.BURN_APPLIED) == 1
    assert outcome_types.count(CombatOutcomeType.BURN_TICK) == 3
    assert outcome_types.count(CombatOutcomeType.BURN_EXPIRED) == 1
    assert tuple(
        outcome.amount
        for outcome in outcomes
        if outcome.outcome_type == CombatOutcomeType.BURN_TICK
    ) == (7, 7, 7)

    ready_cinderwrit = tuple(
        move
        for view in ui.rendered_views
        for move in view.move_options
        if move.name == "Infused Barb" and "Ready: Fire" in move.tags
    )
    assert ready_cinderwrit

    # The displayed log remains turn-scoped even though the test recorder audits history.
    assert tuple(entry.event_type for entry in session.entries) == (
        BattleEventType.DAMAGE,
        BattleEventType.VICTORY,
    )
    assert not any(
        outcome.outcome_type
        in {
            CombatOutcomeType.COMPOUNDS_CONSUMED,
            CombatOutcomeType.CINDERWRIT_PREPARED,
            CombatOutcomeType.INFUSED_BARB_CONSUMED,
            CombatOutcomeType.BURN_TICK,
        }
        for outcome in _outcomes(session.entries)
    )


def test_complete_stock_prepare_loose_poison_goblin_vertical_slice(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda _start, _end: 1)
    monkeypatch.setattr(battle_module.random, "choice", lambda moves: moves[0])
    player = PlayerState(RogueArcher())
    enemy = EnemyState(Goblin())
    ui = ZhaivraLoopUI(first_item="deep_coal", companion="night_berry")
    session = RecordingPresentationSession()
    battle = Battle(
        player,
        enemy,
        ui=ui,
        resolver=CombatResolver(rng=AlwaysOneRng()),
        presentation_session=session,
    )

    winner = battle.run()

    assert winner == "player"
    assert enemy.health.current == 0
    assert player.character_run_state.item_quantity(RunItemId.EMBER_SHARD) == 1
    assert player.character_run_state.item_quantity(RunItemId.DEEP_COAL) == 0
    assert player.character_run_state.item_quantity(RunItemId.NIGHT_BERRY) == 0
    assert player.character_run_state.payload_prepared(
        PreparedPayloadId.CINDERWRIT
    ) is False
    assert battle.combat_state.poison_active(enemy) is False

    outcomes = _outcomes(session.history)
    outcome_types = tuple(outcome.outcome_type for outcome in outcomes)
    assert outcome_types.count(CombatOutcomeType.COMPOUNDS_CONSUMED) == 1
    assert outcome_types.count(CombatOutcomeType.POISON_INFUSION_PREPARED) == 1
    assert outcome_types.count(CombatOutcomeType.INFUSED_BARB_CONSUMED) == 1
    assert outcome_types.count(CombatOutcomeType.POISON_APPLIED) == 1
    assert outcome_types.count(CombatOutcomeType.POISON_TICK) == 4
    assert outcome_types.count(CombatOutcomeType.POISON_EXPIRED) == 1
    assert tuple(
        outcome.amount
        for outcome in outcomes
        if outcome.outcome_type == CombatOutcomeType.POISON_TICK
    ) == (5, 5, 5, 5)

    ready_poison = tuple(
        move
        for view in ui.rendered_views
        for move in view.move_options
        if move.name == "Infused Barb" and "Ready: Poison" in move.tags
    )
    assert ready_poison


def test_run_scarcity_personal_ownership_and_encounter_state_boundaries():
    zhaivra = PlayerState(RogueArcher())
    run_state = zhaivra.character_run_state
    preparation = InventoryActionResolver().resolve(
        "prepare_cinderwrit",
        run_state,
    )
    first_combat_state = CombatState()
    target = EnemyState(Goblin())
    mana_before = zhaivra.mana_resource.current

    rejected = CombatResolver(rng=ScriptedRng()).resolve_move(
        zhaivra,
        zhaivra,
        "Infused Barb",
        combat_state=first_combat_state,
        character_run_state=run_state,
    )
    missed = CombatResolver(rng=ScriptedRng(100)).resolve_move(
        zhaivra,
        target,
        "Infused Barb",
        combat_state=first_combat_state,
        character_run_state=run_state,
    )
    second_preparation = InventoryActionResolver().resolve(
        "prepare_cinderwrit",
        run_state,
    )

    assert preparation.accepted is True
    assert rejected.accepted is False
    assert rejected.reason == "invalid_target_type"
    assert missed.accepted is True
    assert missed.hit is False
    assert mana_before - zhaivra.mana_resource.current == 5
    assert tuple(outcome.outcome_type for outcome in missed.outcomes) == (
        CombatOutcomeType.INFUSED_BARB_CONSUMED,
    )
    assert run_state.payload_prepared(PreparedPayloadId.CINDERWRIT) is False
    assert second_preparation.accepted is False
    assert second_preparation.reason == InventoryActionRejectionReason.MISSING_INGREDIENTS

    next_encounter = Battle(zhaivra, EnemyState(Goblin()), ui=UnusedUI())
    assert next_encounter.player_state.character_run_state is run_state
    assert next_encounter.combat_state.burn_active(target) is False

    branoc = PlayerState(Brawler())
    foreign_preparation = InventoryActionResolver().resolve(
        "prepare_cinderwrit",
        branoc.character_run_state,
    )
    assert foreign_preparation.accepted is False
    assert foreign_preparation.reason == InventoryActionRejectionReason.ACTION_UNAVAILABLE
    assert branoc.character_run_state.item_quantity(RunItemId.EMBER_SHARD) == 0
    assert branoc.character_run_state.item_quantity(RunItemId.DEEP_COAL) == 0

    fresh_run = PlayerState(RogueArcher()).character_run_state
    assert fresh_run.item_quantity(RunItemId.EMBER_SHARD) == 1
    assert fresh_run.item_quantity(RunItemId.DEEP_COAL) == 1


def test_standard_burn_refreshes_to_three_ticks_and_retains_stronger_source():
    weak_source = PlayerState(Brawler())
    strong_source = PlayerState(RogueArcher())
    target = EnemyState(Goblin())
    combat_state = CombatState()

    combat_state.apply_burn(weak_source, target)
    combat_state.complete_accepted_action(target, (weak_source,))
    combat_state.apply_burn(strong_source, target)
    stronger = combat_state.burn_status(target)
    combat_state.complete_accepted_action(target, (strong_source,))
    combat_state.apply_burn(weak_source, target)
    retained = combat_state.burn_status(target)

    assert stronger.source is strong_source
    assert stronger.damage_per_tick == 7
    assert stronger.remaining_ticks == 3
    assert retained.source is strong_source
    assert retained.damage_per_tick == 7
    assert retained.remaining_ticks == 3


def test_branoc_azhvielle_joruun_and_universal_core_paths_remain_compatible():
    target = EnemyState(Goblin())

    branoc = PlayerState(Brawler())
    branoc_state = CombatState()
    brace = CombatResolver(rng=ScriptedRng()).resolve_move(
        branoc,
        branoc,
        "Brace",
        combat_state=branoc_state,
    )
    ironwake = CombatResolver(rng=ScriptedRng(1, 100)).resolve_move(
        branoc,
        target,
        "Ironwake Dismemberment",
        combat_state=branoc_state,
    )

    assert brace.accepted is True
    assert ironwake.accepted is True
    assert branoc_state.brace_follow_up_damage_bonus_percent(
        branoc,
        "heavy_attack",
    ) == 0

    azhvielle = PlayerState(BlackMage())
    azhvielle_state = CombatState()
    gravemantle = CombatResolver(rng=ScriptedRng(1, 100, 100)).resolve_move(
        azhvielle,
        target,
        "Gravemantle Rupture",
        combat_state=azhvielle_state,
    )
    discharge = CombatResolver(rng=ScriptedRng(1, 100)).resolve_move(
        azhvielle,
        target,
        "Gloamweight Sepulcher",
        combat_state=azhvielle_state,
    )

    assert CombatOutcomeType.OVERCHARGE_GAINED in {
        outcome.outcome_type for outcome in gravemantle.outcomes
    }
    assert tuple(outcome.outcome_type for outcome in discharge.outcomes)[:2] == (
        CombatOutcomeType.OVERCHARGE_CONSUMED,
        CombatOutcomeType.BREAK_CLEARED,
    )

    joruun = PlayerState(Monk())
    joruun_state = CombatState()
    ordinary = CombatResolver(rng=ScriptedRng(1, 100)).resolve_move(
        joruun,
        EnemyState(Goblin()),
        "Bring the Horse to Water",
        combat_state=joruun_state,
    )
    defend = CombatResolver(rng=ScriptedRng()).resolve_defend(
        joruun,
        joruun_state,
    )
    joruun.health.take_damage(20)
    healed = CombatResolver(rng=ScriptedRng(10)).resolve_heal(
        joruun,
        combat_state=joruun_state,
    )
    joruun.super_resource.gain(joruun.super_resource.maximum)
    super_result = CombatResolver(rng=ScriptedRng(1, 100)).resolve_move(
        joruun,
        EnemyState(Goblin()),
        "Coagulated Torrent",
        combat_state=joruun_state,
    )

    assert ordinary.accepted is True
    assert defend.accepted is True
    assert healed.accepted is True
    assert healed.healing > 0
    assert super_result.accepted is True
    assert super_result.resource_spent == 100
    assert super_result.outcomes == ()

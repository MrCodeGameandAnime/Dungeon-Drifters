from app.combat.combat_state import CombatState
from app.combat.resolver import CombatResolver
from app.combat.move import (
    DamageType,
    Move,
    MoveKind,
    ResourceType,
    ScalingAttribute,
    TargetType,
)
from app.enemies.goblin.definition import Goblin
from app.enemies.state import EnemyState
from app.player.character import BlackMage, Brawler, RogueArcher
from app.player.player_state import PlayerState
from app.player.inventory_action import InventoryActionResolver
from app.presentation.battle_models import (
    ActionAvailabilityReason,
    ActionIntent,
    BattleEventType,
    BattleLogEntry,
    InteractionPhase,
    MoveAvailabilityReason,
)
from app.presentation.battle_presenter import BattlePresenter


def _battle_values(character=None):
    player = PlayerState(character or Brawler())
    enemy = EnemyState(Goblin())
    combat_state = CombatState()
    return player, enemy, combat_state


def _build(character=None, phase=InteractionPhase.ACTIONS, log_entries=()):
    player, enemy, combat_state = _battle_values(character)
    view = BattlePresenter().build(
        player=player,
        enemy=enemy,
        combat_state=combat_state,
        log_entries=log_entries,
        interaction_phase=phase,
    )
    return view, player, enemy, combat_state


def _option(view, intent):
    return next(option for option in view.action_options if option.intent == intent)


def _move(view, name):
    return next(move for move in view.move_options if move.name == name)


class FixedRng:
    def __init__(self, *rolls):
        self.rolls = list(rolls)

    def randint(self, _start, _end):
        return self.rolls.pop(0)


def test_presenter_builds_resource_and_temporary_state_views():
    player, enemy, combat_state = _battle_values()
    combat_state.activate_defend(player)
    combat_state.activate_brace(player)

    view = BattlePresenter().build(
        player=player,
        enemy=enemy,
        combat_state=combat_state,
    )

    assert (view.player.hp_current, view.player.hp_maximum) == (116, 116)
    assert (view.player.mana_current, view.player.mana_maximum) == (46, 46)
    assert (view.player.super_current, view.player.super_maximum) == (0, 100)
    assert view.player.defending is True
    assert view.player.temporary_labels == ("Defending", "Brace")
    assert (view.enemy.hp_current, view.enemy.hp_maximum) == (60, 60)
    assert view.enemy.mana_current is None
    assert view.enemy.super_current is None


def test_presenter_builds_five_ordinary_action_options():
    view, _, _, _ = _build()

    assert tuple(option.intent for option in view.action_options) == (
        ActionIntent.ATTACK,
        ActionIntent.DEFEND,
        ActionIntent.HEAL,
        ActionIntent.ITEMS,
        ActionIntent.ESCAPE,
    )
    assert tuple(option.number for option in view.action_options) == (1, 2, 3, 4, 5)
    assert _option(view, ActionIntent.ATTACK).enabled is True
    assert _option(view, ActionIntent.DEFEND).enabled is True
    assert _option(view, ActionIntent.HEAL).label == "Heal - Full HP"
    assert _option(view, ActionIntent.HEAL).disabled_reason == ActionAvailabilityReason.FULL_HP
    assert _option(view, ActionIntent.ITEMS).disabled_reason == ActionAvailabilityReason.NOT_IMPLEMENTED
    assert _option(view, ActionIntent.ESCAPE).disabled_reason == ActionAvailabilityReason.NOT_IMPLEMENTED


def test_zhaivra_items_open_personal_inventory_without_mutating_run_state():
    player, enemy, combat_state = _battle_values(RogueArcher())
    before = player.character_run_state.snapshot()
    presenter = BattlePresenter()

    actions = presenter.build(
        player=player,
        enemy=enemy,
        combat_state=combat_state,
    )
    inventory = presenter.build(
        player=player,
        enemy=enemy,
        combat_state=combat_state,
        interaction_phase=InteractionPhase.INVENTORY,
    )
    repeated = presenter.build(
        player=player,
        enemy=enemy,
        combat_state=combat_state,
        interaction_phase=InteractionPhase.INVENTORY,
    )

    assert _option(actions, ActionIntent.ITEMS).enabled is True
    assert inventory.move_options == ()
    assert len(inventory.inventory_options) == 1
    option = inventory.inventory_options[0]
    assert option.action_id == "prepare_cinderwrit"
    assert option.label == "Prepare Cinderwrit Barb"
    assert option.enabled is True
    assert tuple(
        (ingredient.item_id, ingredient.display_name, ingredient.current, ingredient.required)
        for ingredient in option.ingredients
    ) == (
        ("ember_shard", "Ember Shard", 1, 1),
        ("deep_coal", "Deep Coal", 1, 1),
    )
    assert inventory == repeated
    assert player.character_run_state.snapshot() == before


def test_prepared_cinderwrit_inventory_action_is_disabled_without_presenter_mutation():
    player, enemy, combat_state = _battle_values(RogueArcher())
    InventoryActionResolver().resolve("prepare_cinderwrit", player.character_run_state)
    before = player.character_run_state.snapshot()

    view = BattlePresenter().build(
        player=player,
        enemy=enemy,
        combat_state=combat_state,
        interaction_phase=InteractionPhase.INVENTORY,
    )

    option = view.inventory_options[0]
    assert option.enabled is False
    assert option.disabled_reason.value == "already_prepared"
    assert tuple(ingredient.current for ingredient in option.ingredients) == (0, 0)
    assert player.character_run_state.snapshot() == before


def test_missing_compound_disables_preparation_but_keeps_personal_items_visible():
    character = RogueArcher()
    character.starting_run_inventory = {"ember_shard": 1}
    player = PlayerState(character)
    enemy = EnemyState(Goblin())
    combat_state = CombatState()

    actions = BattlePresenter().build(
        player=player,
        enemy=enemy,
        combat_state=combat_state,
    )
    inventory = BattlePresenter().build(
        player=player,
        enemy=enemy,
        combat_state=combat_state,
        interaction_phase=InteractionPhase.INVENTORY,
    )

    assert _option(actions, ActionIntent.ITEMS).enabled is True
    option = inventory.inventory_options[0]
    assert option.enabled is False
    assert option.disabled_reason.value == "missing_ingredients"


def test_universal_heal_is_not_an_authored_move_submenu():
    view, player, _, combat_state = _build()
    player.health.take_damage(10)

    view = BattlePresenter().build(
        player=player,
        enemy=EnemyState(Goblin()),
        combat_state=combat_state,
    )

    assert _option(view, ActionIntent.HEAL).enabled is True
    assert view.move_options == ()


def test_interaction_phase_filters_move_categories():
    actions, _, _, _ = _build(phase=InteractionPhase.ACTIONS)
    regular, _, _, _ = _build(phase=InteractionPhase.REGULAR_MOVES)
    healing, _, _, _ = _build(phase=InteractionPhase.HEALING_MOVES)
    super_moves, _, _, _ = _build(phase=InteractionPhase.SUPER_MOVES)

    assert actions.move_options == ()
    assert tuple(move.name for move in regular.move_options) == (
        "Crestgrave Reaping",
        "Cinderlung Vesper",
        "Brace",
        "Ironwake Dismemberment",
    )
    assert healing.move_options == ()
    assert tuple(move.name for move in super_moves.move_options) == (
        "Third Gate Obsequy",
    )


def test_presenter_composes_authored_tags_summary_and_resource_labels():
    view, _, _, _ = _build(phase=InteractionPhase.REGULAR_MOVES)

    assert _move(view, "Crestgrave Reaping").tags == ("Normal",)
    assert _move(view, "Cinderlung Vesper").tags == ("Fire Magic", "3 Mana")
    assert _move(view, "Brace").tags == ("Utility", "5 Mana")
    assert _move(view, "Brace").rules_summary == (
        "Brace against the next enemy action, reducing physical damage by 40%, "
        "and empower your next Heavy attack by 30%."
    )
    ironwake = _move(view, "Ironwake Dismemberment")
    assert ironwake.tags == ("Heavy",)
    assert ironwake.rules_summary == "A crushing Sunder-Spire strike."
    assert _move(view, "Crestgrave Reaping").rules_summary.startswith("Sunder-Spire")


def test_generic_move_metadata_has_deterministic_fallback():
    view, _, _, _ = _build(BlackMage(), InteractionPhase.REGULAR_MOVES)

    scepter = _move(view, "Scepter Sweep")
    gloamweight = _move(view, "Gloamweight Sepulcher")
    assert scepter.tags == ("Normal",)
    assert scepter.rules_summary == "A direct scepter strike aimed at the target."
    assert gloamweight.tags == ("Normal", "8 Mana")


def test_unaffordable_moves_are_disabled_without_hiding_them():
    player, enemy, combat_state = _battle_values()
    player.mana_resource.spend(player.mana_resource.current)

    view = BattlePresenter().build(
        player=player,
        enemy=enemy,
        combat_state=combat_state,
        interaction_phase=InteractionPhase.REGULAR_MOVES,
    )

    assert _move(view, "Crestgrave Reaping").enabled is True
    assert _move(view, "Cinderlung Vesper").disabled_reason == MoveAvailabilityReason.INSUFFICIENT_RESOURCE
    assert _move(view, "Brace").disabled_reason == MoveAvailabilityReason.INSUFFICIENT_RESOURCE


def test_super_meter_is_persistent_and_ready_only_when_affordable():
    view, player, enemy, combat_state = _build()

    assert (view.super_meter.current, view.super_meter.maximum) == (0, 100)
    assert view.super_meter.fill_bps == 0
    assert view.super_meter.ready is False
    assert view.super_meter.activation_offered is False

    player.super_resource.gain(100)
    ready = BattlePresenter().build(
        player=player,
        enemy=enemy,
        combat_state=combat_state,
        interaction_phase=InteractionPhase.REGULAR_MOVES,
    )
    assert ready.super_meter.fill_bps == 10_000
    assert ready.super_meter.ready is True
    assert ready.super_meter.activation_key == "S"
    assert ready.super_meter.activation_offered is True


def test_brace_follow_up_tag_is_dynamic_non_consuming_and_ordered():
    player, enemy, combat_state = _battle_values()
    combat_state.activate_brace(player)
    presenter = BattlePresenter()

    first = presenter.build(
        player=player,
        enemy=enemy,
        combat_state=combat_state,
        interaction_phase=InteractionPhase.REGULAR_MOVES,
    )
    second = presenter.build(
        player=player,
        enemy=enemy,
        combat_state=combat_state,
        interaction_phase=InteractionPhase.REGULAR_MOVES,
    )

    assert _move(first, "Ironwake Dismemberment").tags == ("Heavy", "Empowered +30%")
    assert first == second
    assert combat_state.brace_follow_up_damage_bonus_percent(player, "heavy_attack") == 30


def test_accepted_heavy_hit_and_miss_remove_empowered_tag():
    for rolls in ((1, 100), (100,)):
        player, enemy, combat_state = _battle_values()
        combat_state.activate_brace(player)
        result = CombatResolver(rng=FixedRng(*rolls)).resolve_move(
            player,
            enemy,
            "Ironwake Dismemberment",
            combat_state=combat_state,
        )

        view = BattlePresenter().build(
            player=player,
            enemy=enemy,
            combat_state=combat_state,
            interaction_phase=InteractionPhase.REGULAR_MOVES,
        )

        assert result.accepted is True
        assert "Empowered +30%" not in _move(view, "Ironwake Dismemberment").tags


def test_rejected_heavy_and_nonmatching_move_preserve_empowered_tag():
    player, enemy, combat_state = _battle_values()
    combat_state.activate_brace(player)
    enemy.health.take_damage(enemy.health.maximum)
    rejected = CombatResolver(rng=FixedRng()).resolve_move(
        player,
        enemy,
        "Ironwake Dismemberment",
        combat_state=combat_state,
    )

    rejected_view = BattlePresenter().build(
        player=player,
        enemy=enemy,
        combat_state=combat_state,
        interaction_phase=InteractionPhase.REGULAR_MOVES,
    )

    assert rejected.accepted is False
    assert "Empowered +30%" in _move(rejected_view, "Ironwake Dismemberment").tags

    player, enemy, combat_state = _battle_values()
    combat_state.activate_brace(player)
    nonmatching = CombatResolver(rng=FixedRng(1, 100)).resolve_move(
        player,
        enemy,
        "Crestgrave Reaping",
        combat_state=combat_state,
    )
    nonmatching_view = BattlePresenter().build(
        player=player,
        enemy=enemy,
        combat_state=combat_state,
        interaction_phase=InteractionPhase.REGULAR_MOVES,
    )

    assert nonmatching.accepted is True
    assert "Empowered +30%" in _move(nonmatching_view, "Ironwake Dismemberment").tags


def test_presenter_preserves_log_snapshot_and_has_no_retained_state():
    entry = BattleLogEntry(BattleEventType.ENCOUNTER_START)
    presenter = BattlePresenter()
    player, enemy, combat_state = _battle_values()

    view = presenter.build(
        player=player,
        enemy=enemy,
        combat_state=combat_state,
        log_entries=(entry,),
    )

    assert view.log_entries == (entry,)
    assert vars(presenter) == {}


def test_presenter_build_does_not_mutate_domain_state():
    player, enemy, combat_state = _battle_values()
    before = (
        player.health.current,
        player.mana_resource.current,
        player.super_resource.current,
        enemy.health.current,
        combat_state.turn_count,
    )

    BattlePresenter().build(
        player=player,
        enemy=enemy,
        combat_state=combat_state,
        interaction_phase=InteractionPhase.REGULAR_MOVES,
    )

    after = (
        player.health.current,
        player.mana_resource.current,
        player.super_resource.current,
        enemy.health.current,
        combat_state.turn_count,
    )
    assert after == before

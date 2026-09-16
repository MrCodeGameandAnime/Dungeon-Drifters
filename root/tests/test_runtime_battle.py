from app.combat.battle import Battle
from app.combat.move import TargetType
from app.combat.resolver import CombatResolver
from app.combat.result import MoveResult
from app.content.catalog import create_drifter, create_enemy_definition
from app.enemies.state import EnemyState
from app.player.inventory_action import InventoryActionResolver
from app.player.player_state import PlayerState
from app.presentation.battle_models import ActionIntent, InteractionPhase
from app.ui.battle_ui import ChooseAction, ChooseMove, ChooseTarget, GoBack


class DeterministicRng:
    def __init__(self, initiative=1):
        self.initiative = initiative
        self.randint_calls = []
        self.choice_calls = []

    def randint(self, start, end):
        self.randint_calls.append((start, end))
        return self.initiative if (start, end) == (1, 2) else 1

    def choice(self, options):
        options = tuple(options)
        self.choice_calls.append(options)
        return options[0]


class AlwaysOneRng(DeterministicRng):
    def randint(self, start, end):
        self.randint_calls.append((start, end))
        return self.initiative if (start, end) == (1, 2) else 1


class PassiveResolver:
    def __init__(self, *, lethal=False):
        self.calls = []
        self.lethal = lethal

    def resolve_move(
        self,
        actor,
        target,
        move_name,
        *,
        combat_state=None,
        character_run_state=None,
    ):
        del combat_state, character_run_state
        self.calls.append((actor, target, move_name))
        damage = target.health.current if self.lethal and target is not actor else 0
        if damage:
            target.health.take_damage(damage)
        return MoveResult(
            accepted=True,
            hit=True,
            move_name=move_name,
            resource_spent=0,
            damage=damage,
            healing=0,
            statuses_applied=(),
            reason=None,
        )

    def resolve_heal(self, actor, *, combat_state=None):
        del actor, combat_state
        return MoveResult(
            accepted=True,
            hit=True,
            move_name="Heal",
            resource_spent=0,
            damage=0,
            healing=0,
            statuses_applied=(),
            reason=None,
        )

    def resolve_defend(self, actor, combat_state):
        del actor, combat_state
        return MoveResult(
            accepted=True,
            hit=True,
            move_name="Defend",
            resource_spent=0,
            damage=0,
            healing=0,
            statuses_applied=(),
            reason=None,
        )


class PlayerOnlyResolver(CombatResolver):
    def resolve_move(
        self,
        actor,
        target,
        move_name,
        *,
        combat_state=None,
        character_run_state=None,
    ):
        if hasattr(actor, "archetype_id"):
            return MoveResult(
                accepted=True,
                hit=True,
                move_name=move_name,
                resource_spent=0,
                damage=0,
                healing=0,
                statuses_applied=(),
                reason=None,
            )
        return super().resolve_move(
            actor,
            target,
            move_name,
            combat_state=combat_state,
            character_run_state=character_run_state,
        )

def make_battle(*, enemies=1, initiative=1, resolver=None):
    player = PlayerState(create_drifter("branoc"))
    enemy_states = tuple(
        EnemyState(create_enemy_definition("goblin")) for _ in range(enemies)
    )
    battle = Battle(
        player,
        enemy_states[0] if enemies == 1 else enemy_states,
        ui=None,
        resolver=resolver or PassiveResolver(),
        rng=DeterministicRng(initiative),
    )
    return battle, player, enemy_states


def first_enemy_move(battle):
    return next(
        move for move in battle.player.combat_moves if move.target is TargetType.ENEMY
    )


def test_step_driven_battle_never_needs_a_ui_and_current_view_is_stable():
    battle, _player, _enemies = make_battle()

    first = battle.current_view()
    rng_calls = tuple(battle.rng.randint_calls)
    second = battle.current_view()

    assert first.interaction_phase is InteractionPhase.ACTIONS
    assert second == first
    assert tuple(battle.rng.randint_calls) == rng_calls == ((1, 2),)


def test_step_driven_battle_preserves_navigation_and_stops_at_target_selection():
    battle, _player, enemies = make_battle(enemies=2)
    move = first_enemy_move(battle)

    view = battle.submit(ChooseAction(ActionIntent.ATTACK))
    assert view.interaction_phase is InteractionPhase.REGULAR_MOVES

    view = battle.submit(ChooseMove(move.name))
    assert view.interaction_phase is InteractionPhase.TARGETS
    assert tuple(option.target_id for option in view.target_options) == (
        "enemy_1",
        "enemy_2",
    )

    view = battle.submit(GoBack())
    assert view.interaction_phase is InteractionPhase.REGULAR_MOVES
    assert battle.resolver.calls == []

    view = battle.submit(ChooseMove(move.name))
    view = battle.submit(ChooseTarget("enemy_2"))
    assert view.interaction_phase is InteractionPhase.ACTIONS
    assert battle.resolver.calls[0][1] is enemies[1]
    assert len(battle.rng.choice_calls) == 2


def test_step_driven_battle_rejects_invalid_input_without_advancing():
    battle, player, _enemies = make_battle()
    before_turn = battle.combat_state.turn_count
    before_health = player.health.current

    view = battle.submit(ChooseTarget("unknown"))

    assert view.interaction_phase is InteractionPhase.ACTIONS
    assert battle.combat_state.turn_count == before_turn
    assert player.health.current == before_health
    assert battle.resolver.calls == []


def test_enemy_first_initiative_is_automatic_before_first_view():
    resolver = PassiveResolver()
    battle, _player, _enemies = make_battle(initiative=2, resolver=resolver)

    view = battle.current_view()

    assert view.interaction_phase is InteractionPhase.ACTIONS
    assert len(resolver.calls) == 1
    assert len(battle.rng.choice_calls) == 1
    assert battle.rng.randint_calls == [(1, 2)]


def test_invalid_submission_consumes_no_additional_rng():
    battle, _player, _enemies = make_battle()
    battle.current_view()
    before = (tuple(battle.rng.randint_calls), tuple(battle.rng.choice_calls))

    battle.submit(ChooseTarget("unknown"))

    assert (tuple(battle.rng.randint_calls), tuple(battle.rng.choice_calls)) == before


def test_step_driven_battle_can_navigate_live_inventory():
    battle, _player, _enemies = make_battle()

    view = battle.submit(ChooseAction(ActionIntent.ITEMS))
    assert view.interaction_phase is InteractionPhase.INVENTORY

    view = battle.submit(GoBack())
    assert view.interaction_phase is InteractionPhase.ACTIONS


def test_enemy_first_step_driven_battle_can_complete_defeat_without_input():
    battle, player, _enemies = make_battle(
        initiative=2,
        resolver=PassiveResolver(lethal=True),
    )

    final = battle.current_view()

    assert battle.is_complete is True
    assert battle.winner == "enemy"
    assert final.interaction_phase is InteractionPhase.COMPLETE
    assert player.health.current == 0


def submit_move(battle, move_name, target_id=None):
    view = battle.submit(ChooseAction(ActionIntent.ATTACK))
    assert view.interaction_phase is InteractionPhase.REGULAR_MOVES
    view = battle.submit(ChooseMove(move_name))
    if view.interaction_phase is InteractionPhase.TARGETS:
        assert target_id is not None
        view = battle.submit(ChooseTarget(target_id))
    return view


def test_step_driven_battle_covers_branoc_brace_and_follow_up():
    player = PlayerState(create_drifter("branoc"))
    rng = AlwaysOneRng()
    battle = Battle(
        player,
        EnemyState(create_enemy_definition("goblin")),
        ui=None,
        resolver=PlayerOnlyResolver(rng=rng),
        rng=rng,
    )

    mana_before = player.mana_resource.current
    submit_move(battle, "Brace")
    assert player.mana_resource.current == mana_before - 5
    assert battle.combat_state.brace_follow_up_damage_bonus_percent(
        player,
        "heavy_attack",
    ) > 0

    submit_move(battle, "Ironwake Dismemberment")
    assert battle.combat_state.brace_follow_up_damage_bonus_percent(
        player,
        "heavy_attack",
    ) == 0


def test_step_driven_battle_covers_azhvielle_gravemantle():
    player = PlayerState(create_drifter("azhvielle"))
    enemy = EnemyState(create_enemy_definition("goblin"))
    rng = AlwaysOneRng()
    battle = Battle(
        player,
        enemy,
        ui=None,
        resolver=CombatResolver(rng=rng),
        rng=rng,
    )

    submit_move(battle, "Gravemantle Rupture")

    assert battle.combat_state.gravemantle_break_active(enemy)
    assert battle.combat_state.arcane_overcharge_active(player)


def test_step_driven_battle_covers_zhaivra_infusion():
    player = PlayerState(create_drifter("zhaivra"))
    preparation = InventoryActionResolver().resolve(
        "prepare_fire_infusion",
        player.character_run_state,
    )
    assert preparation.accepted
    enemy = EnemyState(create_enemy_definition("goblin"))
    rng = AlwaysOneRng()
    battle = Battle(
        player,
        enemy,
        ui=None,
        resolver=CombatResolver(rng=rng),
        rng=rng,
    )

    submit_move(battle, "Infused Barb")

    assert battle.combat_state.burn_active(enemy)
    assert player.character_run_state.prepared_infusion() is None


def test_step_driven_battle_covers_joruun_targeted_lightning_setup():
    player = PlayerState(create_drifter("joruun"))
    first = EnemyState(create_enemy_definition("goblin"))
    second = EnemyState(create_enemy_definition("goblin"))
    rng = AlwaysOneRng()
    battle = Battle(
        player,
        (first, second),
        ui=None,
        resolver=CombatResolver(rng=rng),
        rng=rng,
    )

    submit_move(battle, "Hydro Whip", "enemy_1")
    submit_move(battle, "Tempest Surge", "enemy_1")
    view = submit_move(battle, "Lightning Palm", "enemy_2")

    assert view.interaction_phase is InteractionPhase.ACTIONS
    assert battle.combat_state.conductive_active(player, first)
    assert battle.combat_state.turbulence_active(player, first)
    assert not battle.combat_state.conductive_active(player, second)
    assert not battle.combat_state.turbulence_active(player, second)


def test_step_driven_battle_finishes_with_one_inactive_final_view():
    resolver = PassiveResolver(lethal=True)
    battle, _player, enemies = make_battle(resolver=resolver)
    move = first_enemy_move(battle)

    battle.current_view()
    battle.submit(ChooseAction(ActionIntent.ATTACK))
    battle.submit(ChooseMove(move.name))
    final = battle.submit(ChooseTarget("enemy_1"))

    assert battle.is_complete is True
    assert battle.winner == "player"
    assert final.interaction_phase is InteractionPhase.COMPLETE
    assert final is battle.current_view()
    assert final.action_options == ()
    assert final.move_options == ()
    assert final.target_options == ()
    assert enemies[0].health.current == 0
    assert battle.submit(ChooseAction(ActionIntent.ATTACK)) is final

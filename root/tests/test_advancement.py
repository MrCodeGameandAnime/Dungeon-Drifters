import pytest

from app.content.advancement_spec import (
    ADVANCEMENT_SKILLS,
    AdvancementSkillKind,
    AdvancementSkillSpec,
    build_advancement_catalog,
    get_advancement_skill,
    get_drifter_advancement_skills,
)
from app.content.advancement_combat_spec import get_advancement_move
from app.content.catalog import create_drifter
from app.player.player_state import PlayerState
from app.player.advancement_state import move_id_for_name


DRIFTER_IDS = ("branoc", "azhvielle", "zhaivra", "joruun")


def test_each_drifter_has_the_authored_24_skill_tree():
    assert len(ADVANCEMENT_SKILLS) == 96

    for drifter_id in DRIFTER_IDS:
        skills = get_drifter_advancement_skills(drifter_id)
        assert len(skills) == 24
        assert {skill.slot_id for skill in skills} == {
            *(f"p{index:02d}" for index in range(1, 19)),
            *(f"a{index:02d}" for index in range(1, 7)),
        }
        assert sum(skill.kind is AdvancementSkillKind.PASSIVE for skill in skills) == 18
        assert sum(skill.kind is AdvancementSkillKind.NORMAL_MOVE for skill in skills) == 1
        assert sum(skill.kind is AdvancementSkillKind.MANA_MOVE for skill in skills) == 4
        assert sum(skill.kind is AdvancementSkillKind.SUPER for skill in skills) == 1
        assert sum(skill.gp_cost == 2 for skill in skills) == 18
        assert sum(skill.gp_cost == 3 for skill in skills) == 6


def test_advancement_catalog_rejects_duplicate_or_missing_slots():
    with pytest.raises(ValueError, match="duplicate advancement skill ID"):
        build_advancement_catalog(ADVANCEMENT_SKILLS + (ADVANCEMENT_SKILLS[0],))

    with pytest.raises(ValueError, match="each advancement slot exactly once"):
        build_advancement_catalog(ADVANCEMENT_SKILLS[:-1])

    with pytest.raises(ValueError, match="Drifter IDs must be unique"):
        build_advancement_catalog(
            ADVANCEMENT_SKILLS,
            drifter_ids=DRIFTER_IDS + (DRIFTER_IDS[0],),
        )


@pytest.mark.parametrize(
    ("drifter_id", "slot_id", "message"),
    (
        ("unknown", "p01", "unknown advancement Drifter"),
        ("branoc", "p19", "unknown advancement slot"),
    ),
)
def test_authored_skill_rejects_unknown_owner_or_slot(drifter_id, slot_id, message):
    with pytest.raises(ValueError, match=message):
        AdvancementSkillSpec(drifter_id, slot_id, "Test", "Test purpose")


def test_starting_move_ids_are_stable_and_normalized_without_runtime_regex():
    assert move_id_for_name("branoc", "  Anvil-Line Thrust! ") == (
        "branoc_starting_anvil_line_thrust"
    )


@pytest.mark.parametrize(
    ("skill_id", "kind", "tier", "level", "cost"),
    (
        ("branoc_p01", AdvancementSkillKind.PASSIVE, 1, 1, 2),
        ("azhvielle_a02", AdvancementSkillKind.MANA_MOVE, 2, 25, 3),
        ("zhaivra_a04", AdvancementSkillKind.SUPER, 3, 50, 3),
        ("joruun_p18", AdvancementSkillKind.PASSIVE, 5, 100, 2),
        ("joruun_a06", AdvancementSkillKind.MANA_MOVE, 5, 100, 3),
    ),
)
def test_skill_entries_follow_the_flat_cost_and_tier_contract(
    skill_id,
    kind,
    tier,
    level,
    cost,
):
    skill = get_advancement_skill(skill_id)

    assert skill.kind is kind
    assert skill.tier == tier
    assert skill.minimum_level == level
    assert skill.gp_cost == cost


def _earn_growth_points(player, levels):
    for _ in range(levels):
        player.gain_experience(player.level_state.next_threshold)


def _advancement_state(player):
    return player.snapshot().get("advancement")


def test_passive_purchase_spends_two_points_once_on_exact_drifter():
    branoc = PlayerState(create_drifter("branoc"))
    azhvielle = PlayerState(create_drifter("azhvielle"))
    _earn_growth_points(branoc, 1)

    branoc.purchase_advancement("branoc_p01")

    assert branoc.growth_points == 1
    assert branoc.purchased_passive_skill_ids == ("branoc_p01",)
    assert azhvielle.purchased_passive_skill_ids == ()
    assert azhvielle.growth_points == 0


def test_active_purchase_spends_three_points_and_unlocks_exact_move():
    player = PlayerState(create_drifter("branoc"))
    _earn_growth_points(player, 1)

    player.purchase_advancement("branoc_a01")

    assert player.growth_points == 0
    assert player.purchased_active_skill_ids == ("branoc_a01",)
    assert "branoc_a01" in player.available_normal_move_ids


def test_rejected_advancement_purchases_do_not_mutate_player_state():
    cases = (
        ("branoc_p06", "level"),
        ("branoc_a02", "level"),
        ("azhvielle_p01", "Drifter"),
        ("unknown_p01", "unknown"),
    )
    player = PlayerState(create_drifter("branoc"))
    _earn_growth_points(player, 1)

    for skill_id, message in cases:
        before = player.snapshot()
        with pytest.raises(ValueError, match=message):
            player.purchase_advancement(skill_id)
        assert player.snapshot() == before


def test_duplicate_purchase_and_insufficient_growth_points_are_atomic():
    player = PlayerState(create_drifter("branoc"))
    _earn_growth_points(player, 1)
    player.purchase_advancement("branoc_p01")

    before = player.snapshot()
    with pytest.raises(ValueError, match="already purchased"):
        player.purchase_advancement("branoc_p01")
    assert player.snapshot() == before

    player = PlayerState(create_drifter("branoc"))
    before = player.snapshot()
    with pytest.raises(ValueError, match="Growth Points"):
        player.purchase_advancement("branoc_p01")
    assert player.snapshot() == before


def test_new_active_move_can_be_equipped_without_replacing_legacy_availability():
    player = PlayerState(create_drifter("branoc"))
    _earn_growth_points(player, 1)
    player.purchase_advancement("branoc_a01")
    starting_moves = player.equipped_normal_move_ids

    player.equip_normal_move("branoc_a01", slot=0)

    assert player.equipped_normal_move_ids == (
        "branoc_a01",
        *starting_moves[1:],
    )
    assert set(starting_moves).issubset(player.available_normal_move_ids)


def test_equipped_purchased_skill_move_is_projected_into_combat_pool():
    player = PlayerState(create_drifter("branoc"))
    _earn_growth_points(player, 1)
    player.purchase_advancement("branoc_a01")
    player.equip_normal_move("branoc_a01", slot=0)

    combat_names = tuple(move.name for move in player.combat_moves)

    assert combat_names == (
        "Anvil-Line Thrust",
        "Cinderlung Vesper",
        "Brace",
        "Ironwake Dismemberment",
        "Third Gate Obsequy",
    )


def test_unpurchased_skill_moves_remain_unavailable_to_combat():
    player = PlayerState(create_drifter("branoc"))

    assert "Anvil-Line Thrust" not in {
        move.name for move in player.combat_moves
    }


def test_unpurchased_or_super_move_cannot_be_equipped_as_a_normal_move():
    player = PlayerState(create_drifter("branoc"))

    for move_id in ("branoc_a01", "branoc_a04"):
        before = player.snapshot()
        with pytest.raises(ValueError):
            player.equip_normal_move(move_id, slot=0)
        assert player.snapshot() == before


def test_purchased_super_unlock_is_separate_from_normal_move_slots():
    player = PlayerState(create_drifter("branoc"))
    _earn_growth_points(player, 50)
    original_loadout = player.equipped_normal_move_ids

    player.purchase_advancement("branoc_a04")

    assert "branoc_a04" in player.available_super_move_ids
    assert "branoc_a04" not in player.available_normal_move_ids
    assert player.equipped_normal_move_ids == original_loadout
    assert tuple(move.name for move in player.combat_moves) == (
        "Crestgrave Reaping",
        "Cinderlung Vesper",
        "Brace",
        "Ironwake Dismemberment",
        "Third Gate Obsequy",
        "The Last Crest",
    )


def test_every_authored_active_skill_resolves_to_supported_combat_move():
    from app.combat.resolver import authored_move_rejection_reason

    for skill in ADVANCEMENT_SKILLS:
        if skill.kind is AdvancementSkillKind.PASSIVE:
            continue
        assert authored_move_rejection_reason(
            get_advancement_move(skill.skill_id)
        ) is None


def test_advancement_snapshot_tracks_purchases_and_loadout_separately():
    player = PlayerState(create_drifter("branoc"))
    _earn_growth_points(player, 2)
    player.purchase_advancement("branoc_p01")
    player.purchase_advancement("branoc_a01")
    player.equip_normal_move("branoc_a01", slot=0)

    state = _advancement_state(player)
    assert state["purchased_passive_skill_ids"] == ["branoc_p01"]
    assert state["purchased_active_skill_ids"] == ["branoc_a01"]
    assert state["equipped_normal_move_ids"] == list(
        player.equipped_normal_move_ids
    )

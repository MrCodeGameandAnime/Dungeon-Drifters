from app.items.equipment import EquipmentInstance
from app.persistence.ports import SaveLoadResult
from app.persistence.save_port_contract import SaveLoadStatus
from app.presentation.overworld_models import OverworldAction, OverworldScreen
from app.presentation.overworld_presenter import OverworldPresenter
from app.game.overworld_session import OverworldSession
from app.ui.overworld_ui import (
    ChooseAlchemyRecipe,
    ChooseEquipmentAction,
    ChooseEquipmentInstance,
    ChooseOverworldHealingTarget,
    ChooseOverworldAction,
    ChooseOverworldItem,
)
from tests.game_test_support import completed_hub_game


class AcceptingSavePort:
    def __init__(self):
        self.saved_states = []

    def inspect(self):
        return SaveLoadResult(SaveLoadStatus.MISSING)

    def load(self):
        return SaveLoadResult(SaveLoadStatus.MISSING)

    def save(self, game_state):
        self.saved_states.append(game_state.clone())
        return SaveLoadResult(SaveLoadStatus.SAVED)


def make_session(game, save_port):
    return OverworldSession(
        game,
        battle_factory=lambda *_args, **_kwargs: None,
        enemy_factory=lambda *_args, **_kwargs: None,
        save_port=save_port,
    )


def open_alchemist(session):
    session.submit(ChooseOverworldAction(OverworldAction.VENDORS))
    return session.submit(ChooseOverworldAction(OverworldAction.ALCHEMIST))


def test_alchemist_view_projects_mastery_yield_and_profession_progress():
    game = completed_hub_game()
    economy = game.party_state.hub_economy_state
    economy.add_alchemy_experience(1200)
    game.party_state.add_shared_items({"medicinal_herb": 1, "clean_water": 1})

    view = OverworldPresenter().build(game, screen=OverworldScreen.ALCHEMIST)

    recipe = next(row for row in view.hub_economy.recipes if row.recipe_id == "healing_potion")
    assert (view.hub_economy.alchemy_level, view.hub_economy.alchemy_experience) == (25, 1200)
    assert recipe.output_summary == ("Healing Potion x2",)
    assert recipe.experience_award == 10
    assert recipe.can_craft is True


def test_session_alchemy_craft_persists_output_xp_and_mastery_once():
    game = completed_hub_game()
    game.party_state.hub_economy_state.add_alchemy_experience(1200)
    game.party_state.add_shared_items({"medicinal_herb": 1, "clean_water": 1})
    save_port = AcceptingSavePort()
    session = make_session(game, save_port)
    view = open_alchemist(session)

    crafted = session.submit(
        ChooseAlchemyRecipe(
            "healing_potion",
            expected_transaction_sequence=view.hub_transaction_sequence,
        )
    )

    assert crafted.screen is OverworldScreen.ALCHEMIST
    assert crafted.notice == "Crafted 2 Healing Potions; gained 10 Alchemy XP."
    assert session.game_state.party_state.shared_items == {"healing_potion": 2}
    assert session.game_state.party_state.hub_economy_state.alchemy_experience == 1210
    assert session.game_state.party_state.hub_economy_state.transaction_sequence == 1
    assert len(save_port.saved_states) == 1


def test_return_talisman_craft_requires_confirmation_and_cancel_is_free():
    game = completed_hub_game()
    game.party_state.add_shared_items({"goblin_lord_core": 2, "mythril_plate": 1})
    save_port = AcceptingSavePort()
    session = make_session(game, save_port)
    view = open_alchemist(session)
    before = game.snapshot()

    prompt = session.submit(
        ChooseAlchemyRecipe(
            "return_talisman",
            expected_transaction_sequence=view.hub_transaction_sequence,
        )
    )

    assert prompt.screen is OverworldScreen.ALCHEMY_CONFIRMATION
    assert "2 Goblin Lord Core" in prompt.adventure_text
    assert "1 Mythril Plate" in prompt.adventure_text
    assert session.game_state.snapshot() == before
    assert save_port.saved_states == []

    cancelled = session.submit(ChooseOverworldAction(OverworldAction.CANCEL))

    assert cancelled.screen is OverworldScreen.ALCHEMIST
    assert session.game_state.snapshot() == before
    assert save_port.saved_states == []


def test_return_talisman_confirmation_commits_exactly_once():
    game = completed_hub_game()
    game.party_state.add_shared_items({"goblin_lord_core": 2, "mythril_plate": 1})
    save_port = AcceptingSavePort()
    session = make_session(game, save_port)
    view = open_alchemist(session)
    session.submit(
        ChooseAlchemyRecipe(
            "return_talisman",
            expected_transaction_sequence=view.hub_transaction_sequence,
        )
    )

    crafted = session.submit(ChooseOverworldAction(OverworldAction.CONFIRM))

    assert crafted.screen is OverworldScreen.ALCHEMIST
    assert session.game_state.party_state.shared_items == {"return_talisman": 1}
    assert session.game_state.party_state.hub_economy_state.alchemy_experience == 0
    assert session.game_state.party_state.crafting_experience == 0
    assert session.game_state.party_state.hub_economy_state.transaction_sequence == 1
    assert len(save_port.saved_states) == 1


def test_enchanter_projects_progress_discoveries_and_learned_affix_action():
    game = completed_hub_game()
    game.party_state.add_equipment_instance(
        EquipmentInstance.create(
            instance_id="00000000-0000-4000-8000-000000000901",
            definition_id="field_chest",
            source_id="floor_two_reward_01",
            secured=True,
            stat_bonuses={"constitution": 2},
            rarity="uncommon",
            modifier_slots={},
        )
    )
    economy = game.party_state.hub_economy_state
    economy.add_enchanting_experience(25)
    economy.learn_affix("bastion_grade_i")
    game.party_state.add_shared_gold(100)
    game.party_state.add_shared_items({"grade_i_magic_crystal": 2})

    view = OverworldPresenter().build(
        game,
        screen=OverworldScreen.ENCHANTER,
        selected_character_target_id="branoc",
        selected_equipment_instance_id="00000000-0000-4000-8000-000000000901",
    )

    assert (view.equipment.enchanting_level, view.equipment.enchanting_experience) == (2, 25)
    assert view.equipment.known_affixes == ("Bastion | Grade I",)
    assert any(
        action.operation == "apply_learned_affix"
        and action.affix_id == "bastion_grade_i"
        and action.enabled
        for action in view.equipment.actions
    )


def test_session_applies_learned_affix_through_enchanter_service():
    game = completed_hub_game()
    armor = EquipmentInstance.create(
        instance_id="00000000-0000-4000-8000-000000000902",
        definition_id="field_chest",
        source_id="floor_two_reward_01",
        secured=True,
        stat_bonuses={"constitution": 2},
        rarity="uncommon",
        modifier_slots={},
    )
    game.party_state.add_equipment_instance(armor)
    economy = game.party_state.hub_economy_state
    economy.learn_affix("bastion_grade_i")
    game.party_state.add_shared_gold(100)
    starting_gold = game.party_state.shared_gold
    game.party_state.add_shared_items({"grade_i_magic_crystal": 2})
    save_port = AcceptingSavePort()
    session = make_session(game, save_port)
    session.submit(ChooseOverworldAction(OverworldAction.VENDORS))
    view = session.submit(ChooseOverworldAction(OverworldAction.ENCHANTER))
    session.submit(ChooseEquipmentInstance(armor.instance_id))

    result = session.submit(
        ChooseEquipmentAction(
            target_drifter_id="branoc",
            equipment_instance_id=armor.instance_id,
            operation="apply_learned_affix",
            affix_id="bastion_grade_i",
        )
    )

    assert result.screen is OverworldScreen.ENCHANTER
    assert result.notice == "Applied learned affix Bastion."
    updated = session.game_state.party_state.equipment_instance(armor.instance_id)
    assert updated.modifier_slots == {"I": "bastion_grade_i"}
    assert session.game_state.party_state.shared_items == {}
    assert session.game_state.party_state.shared_gold == starting_gold - 8
    assert session.game_state.party_state.hub_economy_state.enchanting_experience == 10
    assert session.game_state.party_state.hub_economy_state.transaction_sequence == 1
    assert len(save_port.saved_states) == 1


def test_mana_potion_restores_exact_deployed_target_and_consumes_one_unit():
    game = completed_hub_game()
    party = game.party_state
    lead, companion = game.active_party_members
    companion.mana_resource.current = 1
    party.add_shared_items({"mana_potion": 1})
    assert party.load_carried_supplies({"mana_potion": 1})
    before = companion.mana_resource.current

    used = party.use_mana_potion(
        companion,
        deployed_members=game.active_party_members,
    )

    assert used is True
    assert companion.mana_resource.current == before + companion.mana_resource.maximum * 30 // 100
    assert party.carried_items == {}
    assert lead.mana_resource.current == lead.mana_resource.maximum


def test_session_mana_potion_targeting_shows_mana_and_consumes_exactly_once():
    game = completed_hub_game()
    party = game.party_state
    target = game.member_for_drifter_id("azhvielle")
    target.mana_resource.current = 0
    party.add_shared_items({"mana_potion": 1})
    assert party.load_carried_supplies({"mana_potion": 1})
    session = make_session(game, AcceptingSavePort())
    session.submit(ChooseOverworldAction(OverworldAction.ITEMS))
    session.submit(ChooseOverworldItem("carried-item:mana_potion"))

    targets = session.submit(ChooseOverworldAction(OverworldAction.USE))

    assert targets.screen is OverworldScreen.HEALING_TARGETS
    assert tuple(item.drifter_id for item in targets.healing_targets) == ("azhvielle",)
    assert targets.healing_targets[0].mana_current == 0
    assert targets.healing_targets[0].mana_maximum == target.mana_resource.maximum

    used = session.submit(ChooseOverworldHealingTarget("azhvielle"))

    assert used.screen is OverworldScreen.ITEMS
    assert target.mana_resource.current == target.mana_resource.maximum * 30 // 100
    assert session.game_state.party_state.carried_items == {}

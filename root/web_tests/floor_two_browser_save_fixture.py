"""Emit a valid local profile positioned to begin a Floor II smoke journey."""

from pathlib import Path
import sys
from uuid import UUID


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from app.persistence.envelope import build_profile_envelope, serialize_profile_envelope
from app.persistence.save_document import build_save_document
from app.player.progression import xp_required_for_next_level
from game_test_support import completed_hub_game


PROFILE_ID = UUID("d4d4d4d4-0000-4000-8000-000000000001")
CLIENT_SAVE_ID = UUID("d4d4d4d4-0000-4000-8000-000000000002")


def main():
    game = completed_hub_game()
    party = game.party_state
    if party.shared_gold != 10:
        raise AssertionError("the fixture no longer matches the tutorial gold baseline")
    party.start_floor_one_run()
    if not party.complete_floor_one_boss(game.active_party_members):
        raise AssertionError("the fixture could not mark Floor I cleared")
    surface_xp = sum(
        xp_required_for_next_level(level) for level in range(1, 9)
    ) + 68
    game.player_state.gain_experience(surface_xp + 670)
    game.member_for_drifter_id("azhvielle").gain_experience(surface_xp + 671)
    if tuple(member.level_state.current for member in game.active_party_members) != (12, 12):
        raise AssertionError("the fixture no longer matches post-Floor-I Level 12 progression")
    for member, primary_stat in (
        (game.player_state, "strength"),
        (game.member_for_drifter_id("azhvielle"), "intelligence"),
    ):
        if member.growth_points != 33:
            raise AssertionError("the Floor II fixture no longer has its expected Growth Points")
        for _ in range(15):
            member.increase_permanent_stat("constitution")
        while member.growth_points:
            member.increase_permanent_stat(primary_stat)
    party.add_shared_gold(54)
    party.add_shared_items({"healing_potion": 12})
    if not party.load_carried_supplies({"healing_potion": 6}):
        raise AssertionError("the fixture could not load its Floor II healing supplies")
    if party.carried_items != {"healing_potion": 6}:
        raise AssertionError("the fixture did not retain its loaded Floor II healing supplies")
    if party.shared_items != {"healing_potion": 6}:
        raise AssertionError("the fixture did not retain reserve Healing Potions in Hub storage")
    envelope = build_profile_envelope(
        build_save_document(game),
        profile_id=PROFILE_ID,
        client_save_id=CLIENT_SAVE_ID,
    )
    sys.stdout.write(serialize_profile_envelope(envelope).decode("utf-8"))


if __name__ == "__main__":
    main()

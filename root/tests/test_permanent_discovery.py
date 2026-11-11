import pytest

from app.content.permanent_discovery_spec import (
    PermanentDiscoverySource,
    PermanentDiscoveryType,
)
from app.game.permanent_discovery import (
    DiscoveryClaimStatus,
    PermanentDiscoveryService,
)
from app.persistence import save_document
from app.persistence.save_port_contract import SaveLoadStatus
from tests.game_test_support import completed_hub_game, three_member_hub_game
from tests.persistence_test_support import make_test_save_port


SOURCES = (
    PermanentDiscoverySource(
        "ancient_well_floor4_01", PermanentDiscoveryType.ANCIENT_WELL, 5
    ),
    PermanentDiscoverySource(
        "ancient_well_floor4_02", PermanentDiscoveryType.ANCIENT_WELL, 10
    ),
    PermanentDiscoverySource(
        "forgotten_altar_floor5_01", PermanentDiscoveryType.FORGOTTEN_ALTAR, 5
    ),
    PermanentDiscoverySource(
        "forgotten_altar_floor5_02", PermanentDiscoveryType.FORGOTTEN_ALTAR, 10
    ),
    PermanentDiscoverySource(
        "spirit_relic_ruins_03", PermanentDiscoveryType.SPIRIT_RELIC, 3
    ),
)


@pytest.fixture(autouse=True)
def register_controlled_discovery_sources(monkeypatch):
    lookup = save_document.get_known_permanent_discovery_source
    controlled = {source.source_id: source for source in SOURCES}

    def get_known_source(source_id):
        if source_id in controlled:
            return controlled[source_id]
        return lookup(source_id)

    monkeypatch.setattr(
        save_document,
        "get_known_permanent_discovery_source",
        get_known_source,
    )


class _NoOpSavePort:
    def inspect(self):
        return None

    def load(self):
        return None

    def save(self, _game_state):
        return type("Result", (), {"status": SaveLoadStatus.INVALID})()


def service_for(save_port):
    return PermanentDiscoveryService(SOURCES, save_port=save_port or _NoOpSavePort())


def player_value(player, path):
    value = player
    for name in path.split("."):
        value = getattr(value, name)
    return value


@pytest.mark.parametrize(
    ("source_index", "member_index", "attribute", "amount"),
    (
        (0, 0, "health.maximum", 5),
        (1, 1, "health.maximum", 10),
        (2, 0, "mana_resource.maximum", 5),
        (3, 1, "mana_resource.maximum", 10),
        (4, 1, "growth_points", 3),
    ),
)
def test_confirmed_discovery_targets_one_active_drifter_and_claims_atomically(
    tmp_path, source_index, member_index, attribute, amount
):
    game = completed_hub_game()
    active = game.active_party_members
    target = active[member_index]
    other = active[1 - member_index]
    source = SOURCES[source_index]
    before_target = player_value(target, attribute)
    before_other = player_value(other, attribute)
    before_current = (target.health.current, target.mana_resource.current)
    port = make_test_save_port(tmp_path / "profile.json")

    result = service_for(port).consume(
        game,
        source.source_id,
        target.drifter_id,
        confirmed=True,
    )

    assert result.status is DiscoveryClaimStatus.CLAIMED
    assert result.reward_applied is True
    assert player_value(
        result.game_state.member_for_drifter_id(target.drifter_id), attribute
    ) == before_target + amount
    assert player_value(
        result.game_state.member_for_drifter_id(other.drifter_id), attribute
    ) == before_other
    assert source.source_id in result.game_state.world_state.permanent_discovery_claims
    assert source.source_id not in game.world_state.permanent_discovery_claims
    loaded = port.load()
    assert loaded.status is SaveLoadStatus.LOADED
    loaded_target = loaded.game_state.member_for_drifter_id(target.drifter_id)
    assert (loaded_target.health.current, loaded_target.mana_resource.current) == before_current
    assert player_value(loaded_target, attribute) == before_target + amount
    assert loaded.game_state.world_state.permanent_discovery_claims == (
        source.source_id,
    )


def test_discovery_offers_only_the_current_active_party():
    game = three_member_hub_game()
    service = service_for(None)

    targets = service.eligible_targets(game, SOURCES[0].source_id)

    assert targets == game.party_state.active_drifter_ids
    assert "joruun" not in targets


def test_non_active_target_is_rejected_without_mutation(tmp_path):
    game = three_member_hub_game()
    before = game.snapshot()
    port = make_test_save_port(tmp_path / "profile.json")

    result = service_for(port).consume(
        game, SOURCES[0].source_id, "joruun", confirmed=True
    )

    assert result.status is DiscoveryClaimStatus.INVALID_TARGET
    assert result.game_state is game
    assert game.snapshot() == before
    assert port.inspect().status is SaveLoadStatus.MISSING


def test_cancel_keeps_source_unclaimed_and_does_not_save(tmp_path):
    game = completed_hub_game()
    before = game.snapshot()
    port = make_test_save_port(tmp_path / "profile.json")
    service = service_for(port)

    result = service.consume(
        game,
        SOURCES[0].source_id,
        game.party_state.active_drifter_ids[0],
        confirmed=False,
    )

    assert result.status is DiscoveryClaimStatus.CANCELLED
    assert result.game_state is game
    assert game.snapshot() == before
    assert port.inspect().status is SaveLoadStatus.MISSING
    assert service.eligible_targets(game, SOURCES[0].source_id) == (
        game.party_state.active_drifter_ids
    )


def test_repeated_claim_cannot_award_again_after_save_reload(tmp_path):
    game = completed_hub_game()
    port = make_test_save_port(tmp_path / "profile.json")
    service = service_for(port)
    source = SOURCES[0]
    drifter_id = game.party_state.active_drifter_ids[0]
    other_drifter_id = game.party_state.active_drifter_ids[1]

    first = service.consume(game, source.source_id, drifter_id, confirmed=True)
    loaded = port.load().game_state
    other_before = loaded.member_for_drifter_id(other_drifter_id).health.maximum
    assert service.eligible_targets(first.game_state, source.source_id) == ()
    second = service.consume(
        loaded, source.source_id, other_drifter_id, confirmed=True
    )

    assert first.status is DiscoveryClaimStatus.CLAIMED
    assert second.status is DiscoveryClaimStatus.ALREADY_CLAIMED
    assert second.game_state is loaded
    assert (
        second.game_state.member_for_drifter_id(drifter_id).health.maximum
        == first.game_state.member_for_drifter_id(drifter_id).health.maximum
    )
    assert (
        second.game_state.member_for_drifter_id(other_drifter_id).health.maximum
        == other_before
    )


def test_unknown_source_id_is_rejected():
    game = completed_hub_game()
    service = service_for(None)

    with pytest.raises(ValueError, match="unknown permanent discovery"):
        service.eligible_targets(game, "ancient_well_not_authored")


def test_malformed_source_id_is_rejected_without_mutation():
    game = completed_hub_game()
    target = game.party_state.active_drifter_ids[0]
    result = service_for(None).consume(
        game,
        ["not", "an", "id"],
        target,
        confirmed=True,
    )

    assert result.status is DiscoveryClaimStatus.INVALID_SOURCE
    assert result.game_state is game


def test_duplicate_authored_source_ids_are_rejected():
    with pytest.raises(ValueError, match="must be unique"):
        PermanentDiscoveryService((SOURCES[0], SOURCES[0]), save_port=_NoOpSavePort())


@pytest.mark.parametrize(
    ("source_id", "discovery_type", "amount"),
    (
        ("bad id", PermanentDiscoveryType.ANCIENT_WELL, 5),
        ("ancient_well_bad", PermanentDiscoveryType.ANCIENT_WELL, 3),
        ("forgotten_altar_bad", PermanentDiscoveryType.FORGOTTEN_ALTAR, 11),
        ("spirit_relic_bad", PermanentDiscoveryType.SPIRIT_RELIC, 5),
    ),
)
def test_malformed_source_definition_is_rejected(source_id, discovery_type, amount):
    with pytest.raises((TypeError, ValueError)):
        PermanentDiscoverySource(source_id, discovery_type, amount)


def test_failed_save_leaves_reward_and_claim_uncommitted():
    class FailingSavePort:
        def inspect(self):
            return None

        def load(self):
            return None

        def save(self, _game_state):
            return type("Result", (), {"status": SaveLoadStatus.INVALID})()

    game = completed_hub_game()
    before = game.snapshot()
    service = service_for(FailingSavePort())

    result = service.consume(
        game,
        SOURCES[0].source_id,
        game.party_state.active_drifter_ids[0],
        confirmed=True,
    )

    assert result.status is DiscoveryClaimStatus.SAVE_FAILED
    assert result.game_state is game
    assert game.snapshot() == before


def test_failed_save_exception_leaves_reward_and_claim_uncommitted():
    class RaisingSavePort(_NoOpSavePort):
        def save(self, _game_state):
            raise OSError("disk write failed")

    game = completed_hub_game()
    before = game.snapshot()
    result = PermanentDiscoveryService(
        SOURCES,
        save_port=RaisingSavePort(),
    ).consume(
        game,
        SOURCES[0].source_id,
        game.party_state.active_drifter_ids[0],
        confirmed=True,
    )

    assert result.status is DiscoveryClaimStatus.SAVE_FAILED
    assert result.game_state is game
    assert game.snapshot() == before

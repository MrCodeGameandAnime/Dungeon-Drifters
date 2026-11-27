import pytest

from app.presentation.visual_assets import (
    destination_visual_asset_id,
    enemy_visual_asset_id,
)


@pytest.mark.parametrize(
    "destination_id, expected_asset_id",
    (
        ("drowned_reliquary", "m8_art_drowned_reliquary"),
        ("ashen_vault", "m8_art_ashen_vault"),
    ),
)
def test_destination_visual_assets_use_canonical_destination_ids(
    destination_id,
    expected_asset_id,
):
    assert destination_visual_asset_id(destination_id) == expected_asset_id


@pytest.mark.parametrize(
    "archetype_id, expected_asset_id",
    (
        ("reliquary_sentinel", "m8_portrait_reliquary_sentinel"),
        ("brine_oracle", "m8_portrait_brine_oracle"),
        ("drowned_stalker", "m8_portrait_drowned_stalker"),
        ("ashbound_hound", "m8_portrait_ashbound_hound"),
        ("tidebound_curator", "m8_portrait_tidebound_curator"),
        ("ashen_regent", "m8_portrait_ashen_regent"),
    ),
)
def test_enemy_visual_assets_use_canonical_archetype_ids(
    archetype_id,
    expected_asset_id,
):
    assert enemy_visual_asset_id(archetype_id) == expected_asset_id


def test_unmapped_content_has_no_visual_asset():
    assert destination_visual_asset_id("floor_one") is None
    assert enemy_visual_asset_id("goblin") is None

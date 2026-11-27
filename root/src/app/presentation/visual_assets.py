"""Stable visual asset associations for renderer-neutral content views."""


_DESTINATION_VISUAL_ASSETS = {
    "drowned_reliquary": "m8_art_drowned_reliquary",
    "ashen_vault": "m8_art_ashen_vault",
}

_ENEMY_VISUAL_ASSETS = {
    "reliquary_sentinel": "m8_portrait_reliquary_sentinel",
    "brine_oracle": "m8_portrait_brine_oracle",
    "drowned_stalker": "m8_portrait_drowned_stalker",
    "ashbound_hound": "m8_portrait_ashbound_hound",
    "tidebound_curator": "m8_portrait_tidebound_curator",
    "ashen_regent": "m8_portrait_ashen_regent",
}


def destination_visual_asset_id(destination_id):
    return _DESTINATION_VISUAL_ASSETS.get(destination_id)


def enemy_visual_asset_id(archetype_id):
    return _ENEMY_VISUAL_ASSETS.get(archetype_id)

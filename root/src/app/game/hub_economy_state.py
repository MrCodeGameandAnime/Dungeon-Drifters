"""Party-owned M6.5 vendor, profession, and outing state."""

from app.content.vendor_catalog import VENDOR_IDS, VENDOR_MERCHANDISE
from app.snapshot import to_plain_value


_FLOOR_FLAGS = {
    "floor_one": "floor_one_cleared",
    "floor_two": "floor_two_cleared",
    "floor_three": "floor_three_cleared",
}


def new_hub_economy_snapshot(
    *,
    recruited_drifter_ids=(),
    floor_one_cleared=False,
    floor_two_cleared=False,
    floor_three_cleared=False,
):
    state = {
        "alchemy_xp": 0,
        "enchanting_xp": 0,
        "known_affix_ids": [],
        "component_stacks": {},
        "vendor_stock": {vendor_id: {} for vendor_id in VENDOR_IDS},
        "future_stock_queue": [],
        "buyback_records": [],
        "hub_visit_sequence": 0,
        "current_hub_visit_id": None,
        "outing_sequence": 0,
        "active_outing": None,
        "last_settled_outing_id": None,
        "last_replenished_outing_id": None,
        "transaction_sequence": 0,
    }
    clear_flags = {
        "floor_one_cleared": floor_one_cleared,
        "floor_two_cleared": floor_two_cleared,
        "floor_three_cleared": floor_three_cleared,
    }
    _add_unlocked_vendor_stock(state, recruited_drifter_ids, clear_flags)
    return state


def _offer_is_unlocked(offer, recruited_drifter_ids, clear_flags):
    if offer.future_content:
        return False
    if offer.unlock_drifter_id is not None:
        return offer.unlock_drifter_id in recruited_drifter_ids
    if offer.unlock_after_floor is not None:
        flag = _FLOOR_FLAGS.get(offer.unlock_after_floor)
        return flag is not None and clear_flags[flag]
    return True


def _add_unlocked_vendor_stock(state, recruited_drifter_ids, clear_flags):
    recruited = set(recruited_drifter_ids)
    for merchandise in VENDOR_MERCHANDISE:
        for offer in merchandise.offers:
            if not _offer_is_unlocked(offer, recruited, clear_flags):
                continue
            stock = state["vendor_stock"][offer.vendor_id]
            if merchandise.item_id not in stock:
                stock[merchandise.item_id] = offer.initial_stock


class HubEconomyState:
    def __init__(self, snapshot=None):
        self._state = (
            new_hub_economy_snapshot()
            if snapshot is None
            else to_plain_value(snapshot, "party.hub_economy")
        )

    def snapshot(self):
        return to_plain_value(self._state, "party.hub_economy")

    @property
    def current_hub_visit_id(self):
        return self._state["current_hub_visit_id"]

    @property
    def active_outing(self):
        outing = self._state["active_outing"]
        return None if outing is None else to_plain_value(outing)

    def initialize_unlocked_stock(
        self,
        *,
        recruited_drifter_ids=(),
        floor_one_cleared=False,
        floor_two_cleared=False,
        floor_three_cleared=False,
    ):
        clear_flags = {
            "floor_one_cleared": floor_one_cleared,
            "floor_two_cleared": floor_two_cleared,
            "floor_three_cleared": floor_three_cleared,
        }
        _add_unlocked_vendor_stock(self._state, recruited_drifter_ids, clear_flags)

    def begin_hub_visit(self):
        current = self._state["current_hub_visit_id"]
        if current is not None:
            return current
        sequence = self._state["hub_visit_sequence"] + 1
        visit_id = f"hub_visit_{sequence}"
        self._state["hub_visit_sequence"] = sequence
        self._state["current_hub_visit_id"] = visit_id
        return visit_id

    def leave_hub(self):
        self._state["current_hub_visit_id"] = None

    def begin_outing(self, floor_id):
        if floor_id not in {"floor_one", "floor_two", "floor_three"}:
            raise ValueError("outing floor ID is not authored")
        if self._state["active_outing"] is not None:
            raise ValueError("an M6.5 outing is already active")
        sequence = self._state["outing_sequence"] + 1
        outing_id = f"outing_{sequence}"
        self._state["outing_sequence"] = sequence
        self._state["active_outing"] = {
            "outing_id": outing_id,
            "floor_id": floor_id,
            "has_encounter_progress": False,
        }
        self.leave_hub()
        return outing_id

    def mark_encounter_progress(self):
        outing = self._state["active_outing"]
        if outing is None:
            return False
        outing["has_encounter_progress"] = True
        return True

    def settle_outing(self):
        outing = self._state["active_outing"]
        if outing is None:
            return None
        settled = to_plain_value(outing, "party.hub_economy.active_outing")
        self._state["active_outing"] = None
        self._state["last_settled_outing_id"] = settled["outing_id"]
        self.begin_hub_visit()
        return settled

    def cancel_outing(self):
        if self._state["active_outing"] is None:
            return False
        self._state["active_outing"] = None
        return True

    def mark_replenished(self, outing_id):
        self._state["last_replenished_outing_id"] = outing_id


__all__ = ("HubEconomyState", "new_hub_economy_snapshot")

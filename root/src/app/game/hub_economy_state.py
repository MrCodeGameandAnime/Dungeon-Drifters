"""Party-owned M6.5 vendor, profession, and outing state."""

from app.content.vendor_catalog import VENDOR_IDS, VENDOR_MERCHANDISE
from app.iteration import first_or_none
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


def _merchandise_by_id(item_id):
    for merchandise in VENDOR_MERCHANDISE:
        if merchandise.item_id == item_id:
            return merchandise
    return None


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

    @property
    def transaction_sequence(self):
        return self._state["transaction_sequence"]

    def vendor_stock_quantity(self, vendor_id, item_id):
        return self._state["vendor_stock"].get(vendor_id, {}).get(item_id, 0)

    def spend_vendor_stock(self, vendor_id, item_id, quantity):
        stock = self._state["vendor_stock"].get(vendor_id)
        if stock is None or stock.get(item_id, 0) < quantity:
            return False
        stock[item_id] -= quantity
        return True

    def component_quantity(self, component_id):
        return self._state["component_stacks"].get(component_id, 0)

    def add_component(self, component_id, quantity=1):
        if not isinstance(component_id, str) or not component_id:
            raise ValueError("component ID must be nonempty")
        quantity = _positive_quantity(quantity)
        stacks = self._state["component_stacks"]
        stacks[component_id] = stacks.get(component_id, 0) + quantity

    def spend_component(self, component_id, quantity=1):
        quantity = _positive_quantity(quantity)
        stacks = self._state["component_stacks"]
        if stacks.get(component_id, 0) < quantity:
            return False
        remaining = stacks[component_id] - quantity
        if remaining:
            stacks[component_id] = remaining
        else:
            del stacks[component_id]
        return True

    def add_buyback_record(self, record):
        if not isinstance(record, dict):
            raise TypeError("buyback record must be a mapping")
        self._state["buyback_records"].append(to_plain_value(record))

    def buyback_record(self, sale_id):
        for record in self._state["buyback_records"]:
            if record["sale_id"] == sale_id:
                return to_plain_value(record)
        return None

    def update_buyback_record(self, sale_id, *, remaining_quantity):
        for index, record in enumerate(self._state["buyback_records"]):
            if record["sale_id"] != sale_id:
                continue
            if remaining_quantity == 0:
                del self._state["buyback_records"][index]
            else:
                record["remaining_quantity"] = remaining_quantity
            return True
        return False

    def remove_buyback_record(self, sale_id):
        records = self._state["buyback_records"]
        for index, record in enumerate(records):
            if record["sale_id"] == sale_id:
                return records.pop(index)
        return None

    def expire_buybacks(self):
        queue = self._state["future_stock_queue"]
        for record in self._state["buyback_records"]:
            if "equipment_snapshot" in record:
                continue
            merchandise = _merchandise_by_id(record["item_id"])
            if merchandise is None or not merchandise.future_stock_eligible:
                continue
            queue.append(
                {
                    "sale_id": record["sale_id"],
                    "specialist_id": record["vendor_id"],
                    "item_id": record["item_id"],
                    "remaining_quantity": record["remaining_quantity"],
                }
            )
        self._state["buyback_records"] = []

    def advance_transaction(self, expected_sequence):
        if self._state["transaction_sequence"] != expected_sequence:
            return False
        self._state["transaction_sequence"] += 1
        return True

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
        self.expire_buybacks()
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

    def replenish_for_qualifying_return(
        self,
        settled_outing,
        *,
        recruited_drifter_ids,
        floor_one_cleared,
        floor_two_cleared,
        floor_three_cleared,
    ):
        if (
            not isinstance(settled_outing, dict)
            or not settled_outing.get("has_encounter_progress")
            or settled_outing.get("outing_id")
            == self._state["last_replenished_outing_id"]
        ):
            return False

        clear_flags = {
            "floor_one_cleared": floor_one_cleared,
            "floor_two_cleared": floor_two_cleared,
            "floor_three_cleared": floor_three_cleared,
        }
        self.initialize_unlocked_stock(
            recruited_drifter_ids=recruited_drifter_ids,
            **clear_flags,
        )
        recruited = set(recruited_drifter_ids)
        for merchandise in VENDOR_MERCHANDISE:
            for offer in merchandise.offers:
                if (
                    offer.unlock_drifter_id is not None
                    and merchandise.item_id
                    in self._state["vendor_stock"].get(offer.vendor_id, {})
                ):
                    recruited.add(offer.unlock_drifter_id)
        for entry in self._state["future_stock_queue"]:
            remaining = entry["remaining_quantity"]
            merchandise = _merchandise_by_id(entry["item_id"])
            if merchandise is None:
                continue
            vendor_ids = (entry["specialist_id"], "merchant")
            for vendor_id in vendor_ids:
                offer = first_or_none(
                    (
                        offer
                        for offer in merchandise.offers
                        if offer.vendor_id == vendor_id
                    )
                )
                if offer is None or not _offer_is_unlocked(
                    offer, recruited, clear_flags
                ):
                    continue
                stock = self._state["vendor_stock"][vendor_id]
                current = stock.get(entry["item_id"], 0)
                moved = min(remaining, offer.stock_cap - current)
                if moved > 0:
                    stock[entry["item_id"]] = current + moved
                    remaining -= moved
                if remaining == 0:
                    break
            entry["remaining_quantity"] = remaining

        self._state["future_stock_queue"] = [
            entry
            for entry in self._state["future_stock_queue"]
            if entry["remaining_quantity"] > 0
        ]

        for merchandise in VENDOR_MERCHANDISE:
            for offer in merchandise.offers:
                if offer.sale_fed_only or not _offer_is_unlocked(
                    offer, recruited, clear_flags
                ):
                    continue
                stock = self._state["vendor_stock"][offer.vendor_id]
                current = stock.get(merchandise.item_id, 0)
                refill = min(
                    offer.refill_per_qualifying_return,
                    offer.stock_cap - current,
                )
                if refill > 0:
                    stock[merchandise.item_id] = current + refill
        self.mark_replenished(settled_outing["outing_id"])
        return True


def _positive_quantity(quantity):
    if isinstance(quantity, bool) or not isinstance(quantity, int):
        raise TypeError("quantity must be an integer")
    if quantity < 1:
        raise ValueError("quantity must be positive")
    return quantity


__all__ = ("HubEconomyState", "new_hub_economy_snapshot")

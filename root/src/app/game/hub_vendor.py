"""Durable, finite Hub commerce and signature-component transactions."""

from dataclasses import dataclass
from enum import StrEnum

from app.content.catalog import get_weapon_spec
from app.content.equipment_spec import get_equipment_template
from app.content.vendor_catalog import VENDOR_IDS, VENDOR_MERCHANDISE
from app.content.weapon_progression_spec import (
    component_required_clear_flag,
    get_weapon_component_spec,
)
from app.game.game_state import GameState
from app.game.party_state import DungeonPhase
from app.game.hub_economy_state import vendor_offer_is_unlocked
from app.iteration import first_or_none
from app.items.equipment import EquipmentInstance
from app.persistence.save_port_contract import (
    SaveLoadStatus,
    SavePortError,
    is_save_port,
)


class HubVendorStatus(StrEnum):
    PURCHASED = "purchased"
    SOLD = "sold"
    BOUGHT_BACK = "bought_back"
    COMPONENT_INSTALLED = "component_installed"
    COMPONENT_CRAFTED = "component_crafted"
    WEAPON_ACTION_COMPLETED = "weapon_action_completed"
    WEAPON_ACTION_FAILED = "weapon_action_failed"
    STALE_TRANSACTION = "stale_transaction"
    UNAVAILABLE = "unavailable"
    UNAVAILABLE_OFFER = "unavailable_offer"
    OUT_OF_STOCK = "out_of_stock"
    INSUFFICIENT_GOLD = "insufficient_gold"
    INSUFFICIENT_ITEMS = "insufficient_items"
    NOT_SELLABLE = "not_sellable"
    NOT_BUYBACK_ELIGIBLE = "not_buyback_eligible"
    SAVE_FAILED = "save_failed"


@dataclass(frozen=True)
class HubVendorResult:
    status: HubVendorStatus
    game_state: GameState
    item_id: str | None = None
    quantity: int = 0
    gold_delta: int = 0
    sale_id: str | None = None
    detail: object | None = None

    @property
    def success(self):
        return self.status in {
            HubVendorStatus.PURCHASED,
            HubVendorStatus.SOLD,
            HubVendorStatus.BOUGHT_BACK,
            HubVendorStatus.COMPONENT_INSTALLED,
            HubVendorStatus.COMPONENT_CRAFTED,
            HubVendorStatus.WEAPON_ACTION_COMPLETED,
        }


class HubVendorService:
    def __init__(self, *, save_port):
        if not is_save_port(save_port):
            raise TypeError("save_port must satisfy SavePort")
        self._save_port = save_port

    def purchase(
        self,
        game_state,
        *,
        vendor_id,
        item_id,
        quantity,
        expected_transaction_sequence,
    ):
        _require_game_state(game_state)
        quantity = _positive_quantity(quantity)
        status = _transaction_status(
            game_state, vendor_id, expected_transaction_sequence
        )
        if status is not None:
            return _result(status, game_state, item_id, quantity)
        merchandise = _merchandise(item_id)
        offer = _offer(merchandise, vendor_id)
        if offer is None:
            return _result(HubVendorStatus.UNAVAILABLE_OFFER, game_state, item_id, quantity)
        party = game_state.party_state
        if (
            offer.future_content
            or offer.unlock_after_floor is not None
        ) and not vendor_offer_is_unlocked(
            offer,
            tuple(member.drifter_id for member in game_state.recruited_members),
            {
                "floor_one_cleared": party.floor_one_cleared,
                "floor_two_cleared": party.floor_two_cleared,
                "floor_three_cleared": party.floor_three_cleared,
                "floor_four_cleared": party.floor_four_cleared,
            },
        ):
            return _result(HubVendorStatus.UNAVAILABLE_OFFER, game_state, item_id, quantity)
        state = game_state.party_state.hub_economy_state
        available = state.vendor_stock_quantity(vendor_id, item_id)
        if available < quantity:
            return _result(HubVendorStatus.OUT_OF_STOCK, game_state, item_id, quantity)
        cost = offer.unit_price * quantity
        if game_state.party_state.shared_gold < cost:
            return _result(HubVendorStatus.INSUFFICIENT_GOLD, game_state, item_id, quantity)

        candidate = game_state.clone()
        party = candidate.party_state
        candidate_economy = party.hub_economy_state
        if not party.spend_shared_gold(cost):
            return _result(HubVendorStatus.INSUFFICIENT_GOLD, game_state, item_id, quantity)
        if not candidate_economy.spend_vendor_stock(vendor_id, item_id, quantity):
            return _result(HubVendorStatus.OUT_OF_STOCK, game_state, item_id, quantity)
        _receive_merchandise(candidate, merchandise, quantity, vendor_id)
        return self._commit(
            candidate,
            game_state,
            expected_transaction_sequence,
            HubVendorStatus.PURCHASED,
            item_id=item_id,
            quantity=quantity,
            gold_delta=-cost,
        )

    def sell(
        self,
        game_state,
        *,
        vendor_id,
        item_id,
        quantity,
        expected_transaction_sequence,
    ):
        _require_game_state(game_state)
        quantity = _positive_quantity(quantity)
        status = _transaction_status(
            game_state, vendor_id, expected_transaction_sequence
        )
        if status is not None:
            return _result(status, game_state, item_id, quantity)
        merchandise = _merchandise(item_id)
        if merchandise is None:
            return _result(HubVendorStatus.NOT_SELLABLE, game_state, item_id, quantity)
        if merchandise.resale_price is None:
            return _result(HubVendorStatus.NOT_SELLABLE, game_state, item_id, quantity)
        if merchandise.sale_vendor_id != vendor_id:
            return _result(HubVendorStatus.UNAVAILABLE_OFFER, game_state, item_id, quantity)
        if merchandise.category in {"armor", "accessory"}:
            return _result(HubVendorStatus.NOT_SELLABLE, game_state, item_id, quantity)
        party = game_state.party_state
        economy = party.hub_economy_state
        is_component = merchandise.category == "component"
        owned = (
            economy.component_quantity(item_id)
            if is_component
            else party.shared_items.get(item_id, 0)
        )
        if owned < quantity:
            return _result(HubVendorStatus.INSUFFICIENT_ITEMS, game_state, item_id, quantity)

        candidate = game_state.clone()
        candidate_party = candidate.party_state
        candidate_economy = candidate_party.hub_economy_state
        if is_component:
            changed = candidate_economy.spend_component(item_id, quantity)
        else:
            changed = candidate_party.spend_shared_items({item_id: quantity})
        if not changed:
            return _result(HubVendorStatus.INSUFFICIENT_ITEMS, game_state, item_id, quantity)
        payout = merchandise.resale_price
        sale_id = _sale_id(expected_transaction_sequence)
        candidate_party.add_shared_gold(payout * quantity)
        candidate_economy.add_buyback_record(
            {
                "sale_id": sale_id,
                "vendor_id": vendor_id,
                "visit_id": candidate_economy.current_hub_visit_id,
                "item_id": item_id,
                "remaining_quantity": quantity,
                "original_unit_payout": payout,
            }
        )
        return self._commit(
            candidate,
            game_state,
            expected_transaction_sequence,
            HubVendorStatus.SOLD,
            item_id=item_id,
            quantity=quantity,
            gold_delta=payout * quantity,
            sale_id=sale_id,
        )

    def buyback(
        self,
        game_state,
        *,
        vendor_id,
        sale_id,
        quantity=1,
        expected_transaction_sequence,
    ):
        _require_game_state(game_state)
        quantity = _positive_quantity(quantity)
        status = _transaction_status(
            game_state, vendor_id, expected_transaction_sequence
        )
        if status is not None:
            return _result(status, game_state, quantity=quantity, sale_id=sale_id)
        if not isinstance(sale_id, str) or not sale_id:
            raise ValueError("sale_id must be a nonempty string")
        economy = game_state.party_state.hub_economy_state
        record = economy.buyback_record(sale_id)
        if (
            record is None
            or record["vendor_id"] != vendor_id
            or record["visit_id"] != economy.current_hub_visit_id
        ):
            return _result(HubVendorStatus.NOT_BUYBACK_ELIGIBLE, game_state, sale_id=sale_id)
        is_equipment = "equipment_snapshot" in record
        remaining = 1 if is_equipment else record["remaining_quantity"]
        if quantity > remaining or (is_equipment and quantity != 1):
            return _result(HubVendorStatus.NOT_BUYBACK_ELIGIBLE, game_state, sale_id=sale_id)
        cost = record["original_unit_payout"] * quantity
        if game_state.party_state.shared_gold < cost:
            return _result(
                HubVendorStatus.INSUFFICIENT_GOLD,
                game_state,
                record["item_id"],
                quantity,
                sale_id=sale_id,
            )

        candidate = game_state.clone()
        party = candidate.party_state
        candidate_economy = party.hub_economy_state
        if not party.spend_shared_gold(cost):
            return _result(HubVendorStatus.INSUFFICIENT_GOLD, game_state, sale_id=sale_id)
        if is_equipment:
            party.add_equipment_instance(
                EquipmentInstance.from_snapshot(record["equipment_snapshot"])
            )
            candidate._bind_equipment_state()
            candidate_economy.remove_buyback_record(sale_id)
        else:
            merchandise = _merchandise(record["item_id"])
            if merchandise is not None and merchandise.category == "component":
                candidate_economy.add_component(record["item_id"], quantity)
            else:
                party.add_shared_items({record["item_id"]: quantity})
            candidate_economy.update_buyback_record(
                sale_id,
                remaining_quantity=remaining - quantity,
            )
        return self._commit(
            candidate,
            game_state,
            expected_transaction_sequence,
            HubVendorStatus.BOUGHT_BACK,
            item_id=record["item_id"],
            quantity=quantity,
            gold_delta=-cost,
            sale_id=sale_id,
        )

    def install_component(
        self,
        game_state,
        *,
        target_drifter_id,
        component_id,
        expected_transaction_sequence,
    ):
        _require_game_state(game_state)
        status = _transaction_status(
            game_state, "blacksmith", expected_transaction_sequence
        )
        if status is not None:
            return _result(status, game_state, component_id, 1)
        try:
            player = game_state.member_for_drifter_id(target_drifter_id)
            weapon = get_weapon_spec(player.signature_weapon_state.weapon_id)
            component = get_weapon_component_spec(
                weapon.progression,
                component_id,
            )
        except (TypeError, ValueError):
            return _result(HubVendorStatus.UNAVAILABLE, game_state, component_id, 1)
        required_clear_flag = component_required_clear_flag(component)
        if (
            required_clear_flag is not None
            and not getattr(game_state.party_state, required_clear_flag)
        ):
            return _result(HubVendorStatus.UNAVAILABLE, game_state, component_id, 1)
        economy = game_state.party_state.hub_economy_state
        if economy.component_quantity(component_id) < 1:
            return _result(HubVendorStatus.INSUFFICIENT_ITEMS, game_state, component_id, 1)
        weapon_state = player.signature_weapon_state
        if weapon_state.components[component.slot_id] == component_id:
            return _result(HubVendorStatus.UNAVAILABLE, game_state, component_id, 1)

        candidate = game_state.clone()
        target = candidate.member_for_drifter_id(target_drifter_id)
        candidate_economy = candidate.party_state.hub_economy_state
        installed = target.signature_weapon_state.components[component.slot_id]
        if not candidate_economy.spend_component(component_id, 1):
            return _result(HubVendorStatus.INSUFFICIENT_ITEMS, game_state, component_id, 1)
        target.signature_weapon_state.install_component(component.slot_id, component_id)
        candidate_economy.add_component(installed, 1)
        return self._commit(
            candidate,
            game_state,
            expected_transaction_sequence,
            HubVendorStatus.COMPONENT_INSTALLED,
            item_id=component_id,
            quantity=1,
        )

    def craft_component(
        self,
        game_state,
        *,
        target_drifter_id,
        component_id,
        expected_transaction_sequence,
    ):
        from app.game.weapon_progression import WeaponProgressionService

        _require_game_state(game_state)
        status = _transaction_status(
            game_state, "blacksmith", expected_transaction_sequence
        )
        if status is not None:
            return _result(status, game_state, component_id, 1)
        candidate = game_state.clone()
        try:
            target = candidate.member_for_drifter_id(target_drifter_id)
            weapon = get_weapon_spec(target.signature_weapon_state.weapon_id)
            component = get_weapon_component_spec(weapon.progression, component_id)
        except (TypeError, ValueError):
            return _result(HubVendorStatus.UNAVAILABLE, game_state, component_id, 1)
        displaced = target.signature_weapon_state.components[component.slot_id]
        detail = WeaponProgressionService(candidate).craft_component(
            target_drifter_id=target_drifter_id,
            component_id=component_id,
        )
        if not detail.success:
            return HubVendorResult(
                HubVendorStatus.WEAPON_ACTION_FAILED,
                game_state,
                item_id=component_id,
                quantity=1,
                detail=detail,
            )
        candidate.party_state.hub_economy_state.add_component(displaced, 1)
        return self._commit(
            candidate,
            game_state,
            expected_transaction_sequence,
            HubVendorStatus.COMPONENT_CRAFTED,
            item_id=component_id,
            quantity=1,
            detail=detail,
        )

    def improve_slot(
        self,
        game_state,
        *,
        target_drifter_id,
        slot_id,
        expected_transaction_sequence,
    ):
        from app.game.weapon_progression import WeaponProgressionService

        return self._run_weapon_action(
            game_state,
            expected_transaction_sequence,
            lambda candidate: WeaponProgressionService(candidate).improve_slot(
                target_drifter_id=target_drifter_id,
                slot_id=slot_id,
            ),
        )

    def dismantle_materials(
        self,
        game_state,
        *,
        target_drifter_id,
        item_id,
        quantity,
        expected_transaction_sequence,
    ):
        from app.game.weapon_progression import WeaponProgressionService

        quantity = _positive_quantity(quantity)
        return self._run_weapon_action(
            game_state,
            expected_transaction_sequence,
            lambda candidate: WeaponProgressionService(candidate).dismantle(
                target_drifter_id=target_drifter_id,
                item_id=item_id,
                quantity=quantity,
            ),
            item_id=item_id,
            quantity=quantity,
        )

    def attempt_tier_v(self, game_state, *, target_drifter_id, expected_transaction_sequence):
        from app.game.weapon_progression import WeaponProgressionService

        return self._run_weapon_action(
            game_state,
            expected_transaction_sequence,
            lambda candidate: WeaponProgressionService(candidate).attempt_tier_v(
                target_drifter_id=target_drifter_id,
            ),
        )

    def _run_weapon_action(
        self,
        game_state,
        expected_transaction_sequence,
        operation,
        *,
        item_id=None,
        quantity=1,
    ):
        from app.game.weapon_progression import WeaponProgressionResult

        _require_game_state(game_state)
        status = _transaction_status(
            game_state, "blacksmith", expected_transaction_sequence
        )
        if status is not None:
            return _result(status, game_state, item_id, quantity)
        candidate = game_state.clone()
        try:
            detail = operation(candidate)
        except (TypeError, ValueError):
            return _result(HubVendorStatus.UNAVAILABLE, game_state, item_id, quantity)
        if not isinstance(detail, WeaponProgressionResult):
            raise TypeError("weapon progression returned an invalid result")
        if not detail.success and not detail.attempted:
            return HubVendorResult(
                HubVendorStatus.WEAPON_ACTION_FAILED,
                game_state,
                item_id=item_id,
                quantity=quantity,
                detail=detail,
            )
        status = (
            HubVendorStatus.WEAPON_ACTION_COMPLETED
            if detail.success
            else HubVendorStatus.WEAPON_ACTION_FAILED
        )
        return self._commit(
            candidate,
            game_state,
            expected_transaction_sequence,
            status,
            item_id=item_id,
            quantity=quantity,
            detail=detail,
        )

    def _commit(
        self,
        candidate,
        original,
        expected_transaction_sequence,
        success_status,
        *,
        item_id=None,
        quantity=0,
        gold_delta=0,
        sale_id=None,
        detail=None,
    ):
        if not candidate.party_state.hub_economy_state.advance_transaction(
            expected_transaction_sequence
        ):
            return _result(HubVendorStatus.STALE_TRANSACTION, original, item_id, quantity)
        try:
            saved = self._save_port.save(candidate)
        except (OSError, SavePortError, TypeError, ValueError):
            saved = None
        if saved is None or saved.status is not SaveLoadStatus.SAVED:
            return HubVendorResult(
                HubVendorStatus.SAVE_FAILED,
                original,
                item_id=item_id,
                quantity=quantity,
                sale_id=sale_id,
                detail=detail,
            )
        return HubVendorResult(
            success_status,
            candidate,
            item_id=item_id,
            quantity=quantity,
            gold_delta=gold_delta,
            sale_id=sale_id,
            detail=detail,
        )


def _transaction_status(game_state, vendor_id, expected_sequence):
    party = game_state.party_state
    if party.phase not in {DungeonPhase.HUB, DungeonPhase.PARTY_READY}:
        return HubVendorStatus.UNAVAILABLE
    if party.hub_economy_state.current_hub_visit_id is None:
        return HubVendorStatus.UNAVAILABLE
    if not isinstance(vendor_id, str) or vendor_id not in VENDOR_IDS:
        return HubVendorStatus.UNAVAILABLE_OFFER
    if (
        isinstance(expected_sequence, bool)
        or not isinstance(expected_sequence, int)
        or expected_sequence != party.hub_economy_state.transaction_sequence
    ):
        return HubVendorStatus.STALE_TRANSACTION
    return None


def _offer(merchandise, vendor_id):
    if merchandise is None:
        return None
    return first_or_none(
        offer for offer in merchandise.offers if offer.vendor_id == vendor_id
    )


def _merchandise(item_id):
    return first_or_none(
        item for item in VENDOR_MERCHANDISE if item.item_id == item_id
    )


def _receive_merchandise(game_state, merchandise, quantity, vendor_id):
    party = game_state.party_state
    economy = party.hub_economy_state
    if merchandise.category == "component":
        economy.add_component(merchandise.item_id, quantity)
        return
    if merchandise.category in {"armor", "accessory"}:
        template = get_equipment_template(merchandise.item_id)
        stats = {
            stat: minimum
            for stat, minimum, _maximum in template.stat_ranges
        }
        for _ in range(quantity):
            party.add_equipment_instance(
                EquipmentInstance.create(
                    definition_id=merchandise.item_id,
                    source_id=f"vendor_{vendor_id}_{merchandise.item_id}",
                    secured=True,
                    stat_bonuses=stats,
                    rarity=merchandise.equipment_rarity_id,
                )
            )
        game_state._bind_equipment_state()
        return
    party.add_shared_items({merchandise.item_id: quantity})


def _sale_id(sequence):
    return f"sale_{sequence + 1}"


def _result(status, game_state, item_id=None, quantity=0, *, sale_id=None):
    return HubVendorResult(
        status,
        game_state,
        item_id=item_id,
        quantity=quantity,
        sale_id=sale_id,
    )


def _require_game_state(game_state):
    if not isinstance(game_state, GameState):
        raise TypeError("game_state must be a GameState")


def _positive_quantity(quantity):
    if isinstance(quantity, bool) or not isinstance(quantity, int):
        raise TypeError("quantity must be an integer")
    if quantity < 1:
        raise ValueError("quantity must be positive")
    return quantity


__all__ = ("HubVendorResult", "HubVendorService", "HubVendorStatus")

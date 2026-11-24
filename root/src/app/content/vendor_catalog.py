"""Non-operational M6.5 vendor offers and first-clear reward definitions."""

from dataclasses import dataclass

from app.content.armor_spec import ARMOR_RARITIES, MODIFIER_DEFINITIONS
from app.content.catalog import DRIFTER_SPECS, ROUTE_SPECS, WEAPON_SPECS
from app.content.equipment_spec import EQUIPMENT_TEMPLATES
from app.content.hub_economy import SUPPLY_ITEMS
from app.content.route_spec import validate_content_id
from app.content.weapon_progression_spec import (
    MATERIAL_SPECS,
    component_required_clear_flag,
    get_material_spec,
)


VENDOR_IDS = ("merchant", "blacksmith", "alchemist")
RESERVED_MAGIC_CRYSTAL_GRADES = (5,)
MAGIC_CRYSTAL_ITEM_IDS = (
    "grade_i_magic_crystal",
    "grade_ii_magic_crystal",
    "grade_iii_magic_crystal",
    "grade_iv_magic_crystal",
)


@dataclass(frozen=True)
class VendorOfferSpec:
    vendor_id: str
    unit_price: int
    stock_cap: int
    initial_stock: int
    refill_per_qualifying_return: int
    unlock_after_floor: str | None = None
    unlock_drifter_id: str | None = None
    sale_fed_only: bool = False
    future_content: bool = False

    def __post_init__(self):
        if not isinstance(self.vendor_id, str) or not self.vendor_id:
            raise ValueError("vendor_id must be nonempty")
        for field in (
            "unit_price",
            "stock_cap",
            "initial_stock",
            "refill_per_qualifying_return",
        ):
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{field} must be an integer")
            if value < 0:
                raise ValueError(f"{field} must not be negative")
        if self.stock_cap < 1:
            raise ValueError("stock_cap must be positive for a vendor offer")
        if self.initial_stock > self.stock_cap:
            raise ValueError("initial_stock cannot exceed stock_cap")
        if self.refill_per_qualifying_return > self.stock_cap:
            raise ValueError("refill quantity cannot exceed stock_cap")
        for field in ("unlock_after_floor", "unlock_drifter_id"):
            value = getattr(self, field)
            if value is not None and (not isinstance(value, str) or not value):
                raise ValueError(f"{field} must be nonempty or None")
        for field in ("sale_fed_only", "future_content"):
            if not isinstance(getattr(self, field), bool):
                raise TypeError(f"{field} must be a boolean")
        if self.sale_fed_only and (self.initial_stock or self.refill_per_qualifying_return):
            raise ValueError("sale-fed-only offers cannot have authored stock")
        if self.future_content and self.initial_stock:
            raise ValueError("future-content offers cannot start with stock")


@dataclass(frozen=True)
class VendorMerchandiseSpec:
    item_id: str
    category: str
    base_price: int
    offers: tuple[VendorOfferSpec, ...]
    resale_price: int | None = None
    sale_vendor_id: str | None = None
    future_stock_eligible: bool = False
    equipment_rarity_id: str | None = None
    equipment_stat_policy: str | None = None
    equipment_modifier_ids: tuple[str, ...] = ()

    def __post_init__(self):
        if not isinstance(self.item_id, str) or not self.item_id:
            raise ValueError("item_id must be nonempty")
        if not isinstance(self.category, str) or not self.category:
            raise ValueError("category must be nonempty")
        if isinstance(self.base_price, bool) or not isinstance(self.base_price, int):
            raise TypeError("base_price must be an integer")
        if self.base_price < 0:
            raise ValueError("base_price must not be negative")
        if not isinstance(self.offers, tuple) or not self.offers:
            raise ValueError("offers must be a nonempty tuple")
        if not all(isinstance(offer, VendorOfferSpec) for offer in self.offers):
            raise TypeError("offers must contain VendorOfferSpec values")
        if self.resale_price is not None and (
            isinstance(self.resale_price, bool)
            or not isinstance(self.resale_price, int)
            or self.resale_price < 0
        ):
            raise ValueError("resale_price must be a non-negative integer or None")
        if self.sale_vendor_id is not None and (
            not isinstance(self.sale_vendor_id, str) or not self.sale_vendor_id
        ):
            raise ValueError("sale_vendor_id must be nonempty or None")
        if not isinstance(self.future_stock_eligible, bool):
            raise TypeError("future_stock_eligible must be a boolean")
        if not isinstance(self.equipment_modifier_ids, tuple) or not all(
            isinstance(value, str) and value for value in self.equipment_modifier_ids
        ):
            raise TypeError("equipment_modifier_ids must contain string IDs")


@dataclass(frozen=True)
class FirstClearRewardSpec:
    source_id: str
    floor_id: str
    item_id: str
    quantity: int

    def __post_init__(self):
        for field in ("source_id", "floor_id", "item_id"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value:
                raise ValueError(f"{field} must be nonempty")
        validate_content_id("first-clear reward source ID", self.source_id)
        if isinstance(self.quantity, bool) or not isinstance(self.quantity, int):
            raise TypeError("quantity must be an integer")
        if self.quantity < 1:
            raise ValueError("quantity must be positive")


_ALCHEMICAL_PRICES = (
    ("medicinal_herb", 4, 3, 2),
    ("clean_water", 4, 3, 2),
    ("charcoal_dust", 4, 3, 2),
    ("sulfur", 4, 3, 2),
    ("magic_reagent", 8, 6, 4),
    ("aether_dust", 8, 6, 4),
    ("healing_potion", 12, 9, None),
    ("mana_potion", 20, 15, None),
    ("smoke_bomb", 12, 9, None),
)
_MATERIAL_PRICES = {1: 4, 2: 8, 3: 16, 4: 32}
_MATERIAL_UNLOCKS = {
    1: None,
    2: "floor_one",
    3: "floor_two",
    4: "floor_three",
}
_ALCHEMICAL_INGREDIENT_IDS = frozenset(
    {
        "medicinal_herb",
        "clean_water",
        "charcoal_dust",
        "sulfur",
        "magic_reagent",
        "aether_dust",
    }
)
_EXPECTED_VENDORS_BY_CATEGORY = {
    "alchemical": frozenset({"alchemist", "merchant"}),
    "smith_material": frozenset({"blacksmith", "merchant"}),
    "component": frozenset({"blacksmith", "merchant"}),
    "armor": frozenset({"blacksmith", "merchant"}),
    "accessory": frozenset({"merchant"}),
    "general": frozenset({"merchant"}),
    "rare_material": frozenset({"blacksmith"}),
    "crystal": frozenset({"merchant"}),
    "talisman": frozenset({"merchant"}),
}


def _offer(
    vendor_id,
    unit_price,
    stock_cap,
    *,
    initial_stock=None,
    refill=None,
    unlock_after_floor=None,
    unlock_drifter_id=None,
    sale_fed_only=False,
    future_content=False,
):
    if initial_stock is None:
        initial_stock = stock_cap
    if refill is None:
        refill = stock_cap
    return VendorOfferSpec(
        vendor_id,
        unit_price,
        stock_cap,
        initial_stock,
        refill,
        unlock_after_floor,
        unlock_drifter_id,
        sale_fed_only,
        future_content,
    )


def _build_alchemical_merchandise():
    result = []
    for item_id, base_price, alchemist_price, resale_price in _ALCHEMICAL_PRICES:
        ingredient = item_id in _ALCHEMICAL_INGREDIENT_IDS
        cap = 2 if ingredient else 1
        result.append(
            VendorMerchandiseSpec(
                item_id,
                "alchemical",
                base_price,
                (
                    _offer("alchemist", alchemist_price, cap),
                    _offer("merchant", base_price, 1),
                ),
                resale_price=resale_price,
                sale_vendor_id="alchemist" if ingredient else None,
                future_stock_eligible=ingredient,
            )
        )
    return result


def _build_material_merchandise():
    result = []
    for material in MATERIAL_SPECS:
        price = _MATERIAL_PRICES[material.grade]
        cap = 2 if material.grade == 1 else 1
        unlock_after_floor = _MATERIAL_UNLOCKS[material.grade]
        result.append(
            VendorMerchandiseSpec(
                material.item_id,
                "smith_material",
                price,
                (
                    _offer(
                        "blacksmith",
                        price,
                        cap,
                        unlock_after_floor=unlock_after_floor,
                    ),
                    _offer(
                        "merchant",
                        price,
                        1,
                        unlock_after_floor=unlock_after_floor,
                    ),
                ),
                resale_price=price // 2,
                sale_vendor_id="blacksmith",
                future_stock_eligible=True,
            )
        )
    return result


def _build_component_merchandise():
    result = []
    for weapon in WEAPON_SPECS:
        drifter_id = weapon.intended_wielder.lower()
        for component in weapon.progression.components:
            price = 8 if component.is_starting else 20
            required_clear_flag = component_required_clear_flag(component)
            unlock_after_floor = (
                None
                if required_clear_flag is None
                else required_clear_flag.rsplit("_", 1)[0]
            )
            sale_fed_only = (
                required_clear_flag is not None
                and get_material_spec(component.recipe_material_id).grade > 1
            )
            result.append(
                VendorMerchandiseSpec(
                    component.component_id,
                    "component",
                    price,
                    (
                        _offer(
                            "blacksmith",
                            price,
                            1,
                            initial_stock=0 if sale_fed_only else None,
                            refill=0 if sale_fed_only else None,
                            unlock_after_floor=unlock_after_floor,
                            unlock_drifter_id=drifter_id,
                            sale_fed_only=sale_fed_only,
                        ),
                        _offer(
                            "merchant",
                            price,
                            1,
                            initial_stock=0 if sale_fed_only else None,
                            refill=0 if sale_fed_only else None,
                            unlock_after_floor=unlock_after_floor,
                            unlock_drifter_id=drifter_id,
                            sale_fed_only=sale_fed_only,
                        ),
                    ),
                    resale_price=price // 2,
                    sale_vendor_id="blacksmith",
                    future_stock_eligible=True,
                )
            )
    return result


def _build_equipment_merchandise():
    prices = {
        "field_helm": (24, 6),
        "field_chest": (40, 10),
        "field_gloves": (24, 6),
        "field_boots": (24, 6),
        "iron_ring": (20, None),
        "wayfinder_pendant": (20, None),
    }
    result = []
    for template in EQUIPMENT_TEMPLATES:
        price, resale_price = prices[template.definition_id]
        armor = template.category == "armor"
        vendors = ("blacksmith", "merchant") if armor else ("merchant",)
        result.append(
            VendorMerchandiseSpec(
                template.definition_id,
                template.category,
                price,
                tuple(_offer(vendor_id, price, 1) for vendor_id in vendors),
                resale_price=resale_price,
                sale_vendor_id="blacksmith" if armor else None,
                future_stock_eligible=False,
                equipment_rarity_id="common" if armor else None,
                equipment_stat_policy="minimum" if armor else "fixed_authored",
            )
        )
    return result


def _build_crystal_merchandise():
    result = []
    for grade, item_id, price, unlock_after_floor in (
        (1, "grade_i_magic_crystal", 12, "floor_one"),
        (2, "grade_ii_magic_crystal", 24, "floor_two"),
        (3, "grade_iii_magic_crystal", 48, "floor_three"),
        (4, "grade_iv_magic_crystal", 96, "floor_four"),
    ):
        future_content = grade == 4
        result.append(
            VendorMerchandiseSpec(
                item_id,
                "crystal",
                price,
                (
                    _offer(
                        "merchant",
                        price,
                        1,
                        initial_stock=0 if future_content else 1,
                        unlock_after_floor=unlock_after_floor,
                        future_content=future_content,
                    ),
                ),
            )
        )
    return result


VENDOR_MERCHANDISE = tuple(
    _build_alchemical_merchandise()
    + _build_material_merchandise()
    + [
        VendorMerchandiseSpec(
            "goblin_scrap",
            "general",
            3,
            (_offer("merchant", 3, 1),),
            resale_price=1,
            sale_vendor_id="merchant",
        ),
        VendorMerchandiseSpec(
            "mythril_plate",
            "rare_material",
            80,
            (
                _offer(
                    "blacksmith",
                    80,
                    1,
                    initial_stock=0,
                    refill=0,
                    sale_fed_only=True,
                ),
            ),
            resale_price=40,
            sale_vendor_id="blacksmith",
            future_stock_eligible=True,
        ),
    ]
    + _build_crystal_merchandise()
    + _build_component_merchandise()
    + _build_equipment_merchandise()
    + [
        VendorMerchandiseSpec(
            "return_talisman",
            "talisman",
            80,
            (_offer("merchant", 100, 1),),
        )
    ]
)


FIRST_CLEAR_REWARDS = (
    FirstClearRewardSpec(
        "m65_floor_one_crystal",
        "floor_one",
        "grade_i_magic_crystal",
        1,
    ),
    FirstClearRewardSpec(
        "m65_floor_two_crystal",
        "floor_two",
        "grade_ii_magic_crystal",
        1,
    ),
    FirstClearRewardSpec(
        "m65_floor_two_mythril",
        "floor_two",
        "mythril_plate",
        1,
    ),
    FirstClearRewardSpec(
        "m65_floor_three_crystal",
        "floor_three",
        "grade_iii_magic_crystal",
        1,
    ),
    FirstClearRewardSpec(
        "m8_floor_four_first_clear_crystal",
        "floor_four",
        "grade_iv_magic_crystal",
        1,
    ),
)


def validate_vendor_catalog(merchandise=None, first_clear_rewards=None):
    """Validate offer identity, source references, eligibility, and stock data."""
    if merchandise is None:
        merchandise = VENDOR_MERCHANDISE
    if first_clear_rewards is None:
        first_clear_rewards = FIRST_CLEAR_REWARDS
    if not isinstance(merchandise, (tuple, list)):
        raise TypeError("vendor merchandise must be a sequence")
    if not isinstance(first_clear_rewards, (tuple, list)):
        raise TypeError("first-clear rewards must be a sequence")

    supplies = {item.item_id: item for item in SUPPLY_ITEMS}
    materials = {material.item_id: material for material in MATERIAL_SPECS}
    components = {
        component.component_id: weapon.intended_wielder.lower()
        for weapon in WEAPON_SPECS
        for component in weapon.progression.components
    }
    equipment = {template.definition_id: template for template in EQUIPMENT_TEMPLATES}
    routes = {route.route_id for route in ROUTE_SPECS}
    drifters = {drifter.drifter_id for drifter in DRIFTER_SPECS}
    rarities = {rarity.rarity_id for rarity in ARMOR_RARITIES}
    modifiers = {modifier.modifier_id for modifier in MODIFIER_DEFINITIONS}
    item_ids = set()

    for spec in merchandise:
        if not isinstance(spec, VendorMerchandiseSpec):
            raise TypeError("vendor merchandise must contain VendorMerchandiseSpec values")
        if spec.item_id in item_ids:
            raise ValueError(f"duplicate vendor merchandise item ID: {spec.item_id}")
        item_ids.add(spec.item_id)
        if spec.category not in _EXPECTED_VENDORS_BY_CATEGORY:
            raise ValueError(f"unknown vendor merchandise category: {spec.category}")
        if not (
            spec.item_id in supplies
            or spec.item_id in materials
            or spec.item_id in components
            or spec.item_id in equipment
        ):
            raise ValueError(f"vendor offer references unknown item ID: {spec.item_id}")
        supply = supplies.get(spec.item_id)
        if supply is not None and supply.base_price != spec.base_price:
            raise ValueError(f"vendor base price disagrees with item definition: {spec.item_id}")
        if spec.resale_price is None:
            if spec.sale_vendor_id is not None or spec.future_stock_eligible:
                raise ValueError("unsellable merchandise cannot define a sale route or future stock")
        else:
            if spec.sale_vendor_id not in VENDOR_IDS:
                raise ValueError("sellable merchandise must name an eligible vendor")
            if spec.resale_price > spec.base_price // 2:
                raise ValueError("resale payout cannot exceed half the base price")
            if spec.future_stock_eligible and spec.sale_vendor_id == "merchant":
                raise ValueError("general Merchant sales do not enter the future-stock queue")

        offers = tuple(spec.offers)
        offer_vendors = tuple(offer.vendor_id for offer in offers)
        if len(set(offer_vendors)) != len(offer_vendors):
            raise ValueError(f"duplicate vendor offer for {spec.item_id}")
        expected_vendors = _EXPECTED_VENDORS_BY_CATEGORY[spec.category]
        if set(offer_vendors) != expected_vendors:
            raise ValueError(f"vendor eligibility mismatch for {spec.item_id}")
        for offer in offers:
            if offer.vendor_id not in VENDOR_IDS:
                raise ValueError(f"unknown merchandise vendor: {offer.vendor_id}")
            if offer.unlock_after_floor is not None:
                if offer.future_content:
                    if offer.unlock_after_floor != "floor_four":
                        raise ValueError("only the Grade-IV Crystal offer is future floor content")
                elif (
                    offer.unlock_after_floor not in routes
                    and offer.unlock_after_floor != "floor_four"
                ):
                    raise ValueError(f"unknown vendor unlock floor: {offer.unlock_after_floor}")
            if offer.unlock_drifter_id is not None:
                if offer.unlock_drifter_id not in drifters:
                    raise ValueError(f"unknown vendor unlock Drifter: {offer.unlock_drifter_id}")
                if spec.category != "component":
                    raise ValueError("only weapon components use a Drifter recruitment unlock")
            if offer.future_content and spec.item_id != "grade_iv_magic_crystal":
                raise ValueError("only Grade-IV Crystal content is reserved for a future floor")
            if offer.sale_fed_only and not spec.future_stock_eligible:
                raise ValueError("sale-fed stock requires an eligible player-sale queue")
            if not offer.sale_fed_only and offer.refill_per_qualifying_return != offer.stock_cap:
                raise ValueError("authored stock refills must top up to the per-vendor cap")
            expected_price = spec.base_price
            if offer.vendor_id == "alchemist":
                if spec.category != "alchemical":
                    raise ValueError("the Alchemist may offer only alchemical merchandise")
                if offer.unit_price * 4 != spec.base_price * 3:
                    raise ValueError("Alchemist prices must apply the exact 25% discount")
            elif offer.vendor_id == "merchant" and spec.category == "talisman":
                if offer.unit_price * 4 != spec.base_price * 5:
                    raise ValueError("Return Talisman must use the approved exact 25% markup")
            elif offer.unit_price != expected_price:
                raise ValueError(f"vendor price disagrees with base price: {spec.item_id}")

        if spec.item_id in components:
            if spec.category != "component":
                raise ValueError(f"weapon component has the wrong merchandise category: {spec.item_id}")
            if spec.resale_price != spec.base_price // 2 or spec.sale_vendor_id != "blacksmith":
                raise ValueError(f"weapon component sale contract is invalid: {spec.item_id}")
            component = next(
                component
                for weapon in WEAPON_SPECS
                for component in weapon.progression.components
                if component.component_id == spec.item_id
            )
            required_clear_flag = component_required_clear_flag(component)
            required_floor = (
                None
                if required_clear_flag is None
                else required_clear_flag.rsplit("_", 1)[0]
            )
            higher_grade = (
                component.recipe_material_id is not None
                and get_material_spec(component.recipe_material_id).grade > 1
            )
            for offer in offers:
                if offer.unlock_drifter_id != components[spec.item_id]:
                    raise ValueError(f"component offer unlock does not match its wielder: {spec.item_id}")
                if offer.unlock_after_floor != required_floor:
                    raise ValueError(f"component offer floor unlock is invalid: {spec.item_id}")
                if higher_grade and (
                    not offer.sale_fed_only
                    or offer.initial_stock != 0
                    or offer.refill_per_qualifying_return != 0
                ):
                    raise ValueError(f"higher-grade component stock must be sale-fed: {spec.item_id}")
                if not higher_grade and offer.sale_fed_only:
                    raise ValueError(f"Grade-I component commerce must remain unchanged: {spec.item_id}")
        elif spec.item_id in equipment:
            template = equipment[spec.item_id]
            expected_category = template.category
            if spec.category != expected_category:
                raise ValueError(f"equipment offer has the wrong category: {spec.item_id}")
            if template.is_armor:
                if (
                    spec.equipment_rarity_id != "common"
                    or spec.equipment_rarity_id not in rarities
                    or spec.equipment_stat_policy != "minimum"
                    or spec.sale_vendor_id != "blacksmith"
                    or spec.resale_price != template.sale_value_gold
                ):
                    raise ValueError(f"armor offer must use its fixed common authored sale contract: {spec.item_id}")
            elif (
                spec.equipment_rarity_id is not None
                or spec.equipment_stat_policy != "fixed_authored"
                or spec.resale_price is not None
                or spec.sale_vendor_id is not None
                or spec.future_stock_eligible
            ):
                raise ValueError(f"accessory offer must remain fixed and non-sellable: {spec.item_id}")
            if spec.equipment_modifier_ids:
                if any(modifier_id not in modifiers for modifier_id in spec.equipment_modifier_ids):
                    raise ValueError(f"equipment offer references an unknown modifier: {spec.item_id}")
                raise ValueError("Slice A equipment offers cannot add modifiers")
        elif spec.category == "smith_material":
            if spec.item_id not in materials or spec.sale_vendor_id != "blacksmith":
                raise ValueError(f"smith material offer is invalid: {spec.item_id}")
            if spec.resale_price != spec.base_price // 2:
                raise ValueError(f"smith material resale must be half base price: {spec.item_id}")
        elif spec.category == "alchemical":
            if spec.item_id not in supplies:
                raise ValueError(f"alchemical merchandise must have an item definition: {spec.item_id}")
            if spec.item_id in _ALCHEMICAL_INGREDIENT_IDS:
                if (
                    spec.sale_vendor_id != "alchemist"
                    or spec.resale_price != spec.base_price // 2
                    or not spec.future_stock_eligible
                ):
                    raise ValueError(f"alchemical ingredient sale route is invalid: {spec.item_id}")
            elif spec.resale_price is not None or supply.sellable:
                raise ValueError(f"finished Alchemy outputs cannot be sold: {spec.item_id}")
        elif spec.category == "crystal":
            if spec.item_id not in MAGIC_CRYSTAL_ITEM_IDS or spec.resale_price is not None:
                raise ValueError(f"Magic Crystal merchandise is invalid: {spec.item_id}")
        elif spec.category == "talisman":
            if spec.item_id != "return_talisman" or spec.sale_vendor_id is not None:
                raise ValueError("Return Talisman is Merchant-only and non-sellable")
        elif spec.category == "rare_material":
            if (
                spec.item_id != "mythril_plate"
                or spec.sale_vendor_id != "blacksmith"
                or spec.resale_price != spec.base_price // 2
                or not spec.future_stock_eligible
                or not all(offer.sale_fed_only for offer in offers)
            ):
                raise ValueError("Mythril Plate must remain rare, Blacksmith-only, and sale-fed")
        elif spec.category == "general":
            if spec.item_id != "goblin_scrap" or spec.sale_vendor_id != "merchant":
                raise ValueError("general merchandise sale route is invalid")

    expected_alchemical = {item_id for item_id, *_ in _ALCHEMICAL_PRICES}
    actual_alchemical = {
        spec.item_id for spec in merchandise if spec.category == "alchemical"
    }
    if actual_alchemical != expected_alchemical:
        raise ValueError("vendor catalog must define the complete approved alchemical schedule")
    if {spec.item_id for spec in merchandise if spec.category == "smith_material"} != set(materials):
        raise ValueError("vendor catalog must offer every authored weapon progression material")
    if {spec.item_id for spec in merchandise if spec.category == "component"} != set(components):
        raise ValueError("vendor catalog must offer every authored weapon component")
    if {spec.item_id for spec in merchandise if spec.category in {"armor", "accessory"}} != set(equipment):
        raise ValueError("vendor catalog must offer every authored equipment template")
    if {spec.item_id for spec in merchandise if spec.category == "crystal"} != set(MAGIC_CRYSTAL_ITEM_IDS):
        raise ValueError("vendor catalog must define Grade I-IV Crystal offers only")

    if not isinstance(first_clear_rewards, (tuple, list)) or not all(
        isinstance(reward, FirstClearRewardSpec) for reward in first_clear_rewards
    ):
        raise TypeError("first-clear rewards must contain FirstClearRewardSpec values")
    source_items = set()
    source_ids = set()
    for reward in first_clear_rewards:
        key = reward.source_id, reward.item_id
        if key in source_items:
            raise ValueError("first-clear reward source/item pairs must be unique")
        if reward.source_id in source_ids:
            raise ValueError("first-clear reward source IDs must be unique")
        source_items.add(key)
        source_ids.add(reward.source_id)
        if reward.floor_id not in routes:
            raise ValueError(f"first-clear reward references unknown floor: {reward.floor_id}")
        if reward.item_id not in supplies:
            raise ValueError(f"first-clear reward references unknown item: {reward.item_id}")
    expected_rewards = {
        ("m65_floor_one_crystal", "floor_one", "grade_i_magic_crystal", 1),
        ("m65_floor_two_crystal", "floor_two", "grade_ii_magic_crystal", 1),
        ("m65_floor_two_mythril", "floor_two", "mythril_plate", 1),
        ("m65_floor_three_crystal", "floor_three", "grade_iii_magic_crystal", 1),
        (
            "m8_floor_four_first_clear_crystal",
            "floor_four",
            "grade_iv_magic_crystal",
            1,
        ),
    }
    if {
        (reward.source_id, reward.floor_id, reward.item_id, reward.quantity)
        for reward in first_clear_rewards
    } != expected_rewards:
        raise ValueError("first-clear reward sources do not match the approved Floor I-IV schedule")
    if "grade_v_magic_crystal" in supplies or any(
        spec.item_id == "grade_v_magic_crystal" for spec in merchandise
    ):
        raise ValueError("Grade-V Magic Crystal is reserved and unavailable")

    return tuple(merchandise)


validate_vendor_catalog()


__all__ = (
    "FIRST_CLEAR_REWARDS",
    "MAGIC_CRYSTAL_ITEM_IDS",
    "RESERVED_MAGIC_CRYSTAL_GRADES",
    "VENDOR_IDS",
    "VENDOR_MERCHANDISE",
    "FirstClearRewardSpec",
    "VendorMerchandiseSpec",
    "VendorOfferSpec",
    "validate_vendor_catalog",
)

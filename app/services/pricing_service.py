"""Load validation and dynamic pricing rules (BR-01 through BR-08, optional BR-29/BR-30)."""

from decimal import Decimal

from config import (
    DEFAULT_EXTRA_STOP_FEE,
    DEFAULT_FUEL_INDEX_PCT,
    MIN_KM,
    RATES,
    RETURN_LOAD_RADIUS_KM,
    SURGE_SUPPLY_RADIUS_KM,
)
from app.models.entities import Load, Truck
from app.services.exceptions import D, RuleError, lane_km, rupee

VALID_MATERIALS = {"GENERAL", "HAZARDOUS", "PERISHABLE", "OVERSIZE"}
MATERIAL_SURCHARGE = {
    "HAZARDOUS": Decimal("0.15"),
    "PERISHABLE": Decimal("0.10"),
}


def validate_load(load: Load) -> None:
    """Validate load weight, truck type, pickup window, and material constraints (BR-08)."""
    if load.weight_tonnes <= 0:
        raise RuleError("Load weight must be positive")
    if load.truck_type not in RATES:
        raise RuleError(f"Unsupported truck type: {load.truck_type}")
    if load.pickup_end < load.pickup_start:
        raise RuleError("Invalid pickup window: pickup_end before pickup_start")
    if load.material not in VALID_MATERIALS:
        raise RuleError(f"Invalid material class: {load.material}")
    if load.material == "PERISHABLE" and (load.pickup_end - load.pickup_start) > 360:
        raise RuleError("Perishable pickup window must be at most 6 hours (360 minutes)")


def calculate_surge_modifier(ratio: Decimal) -> Decimal:
    """Return demand-supply surge percentage modifier (BR-04, strict > and <0.5 thresholds)."""
    if ratio > Decimal("4"):
        return Decimal("0.30")
    if ratio > Decimal("2.5"):
        return Decimal("0.20")
    if ratio > Decimal("1.5"):
        return Decimal("0.10")
    if ratio < Decimal("0.5"):
        return Decimal("-0.10")
    return Decimal("0")


def price_load(
    load: Load,
    trucks: list[Truck],
    loads: list[Load],
    distances: dict[tuple[str, str], int | float | Decimal],
    poor_cities: set[str],
    fuel_index_pct: Decimal = DEFAULT_FUEL_INDEX_PCT,
    extra_stop_fee: Decimal = DEFAULT_EXTRA_STOP_FEE,
) -> dict:
    """Compute dynamic freight pricing breakdown for a load (BR-01..BR-08, BR-29/BR-30)."""
    validate_load(load)
    km = lane_km(distances, load.origin, load.destination)
    charge_km = max(km, MIN_KM)
    base = charge_km * RATES[load.truck_type]

    # BR-03: Active same-type trucks within 200 km of origin
    available = []
    for truck in trucks:
        if truck.active and truck.truck_type == load.truck_type:
            try:
                if lane_km(distances, truck.city, load.origin) <= SURGE_SUPPLY_RADIUS_KM:
                    available.append(truck)
            except RuleError:
                pass

    demand = sum(
        1
        for other in loads
        if other.open and other.origin == load.origin and other.truck_type == load.truck_type
    )
    ratio = D(demand) / D(len(available)) if available else (D("999999") if demand else D("0"))
    surge = calculate_surge_modifier(ratio)

    # BR-05: At least 3 qualifying return loads of same type within 300 km of original origin
    backhaul_count = 0
    for other in loads:
        if (
            other.id == load.id
            or not other.open
            or other.origin != load.destination
            or other.truck_type != load.truck_type
        ):
            continue
        try:
            if lane_km(distances, other.destination, load.origin) <= RETURN_LOAD_RADIUS_KM:
                backhaul_count += 1
        except RuleError:
            pass
    backhaul = Decimal("-0.08") if backhaul_count >= 3 else Decimal("0")

    # BR-06 & BR-07/08: Backhaul-poor destination and material modifiers
    poor = Decimal("0.12") if load.destination in poor_cities else Decimal("0")
    material = MATERIAL_SURCHARGE.get(load.material, Decimal("0"))

    # Optional BR-30 stretch: monthly fuel index adjustment (0 at baseline)
    fuel_adj = D(fuel_index_pct) / Decimal("100")

    total_pct = surge + backhaul + poor + material + fuel_adj
    multi_drop_fee = D(max(0, int(load.extra_stops))) * D(extra_stop_fee)

    recommended = rupee(base * (Decimal("1") + total_pct) + multi_drop_fee)
    load.recommended = recommended
    load.price = {
        "load_id": load.id,
        "origin": load.origin,
        "destination": load.destination,
        "truck_type": load.truck_type,
        "material": load.material,
        "distance_km": km,
        "chargeable_km": charge_km,
        "rate_per_km": RATES[load.truck_type],
        "base_price": rupee(base),
        "open_loads": demand,
        "available_trucks_200km": len(available),
        "demand_supply_ratio": ratio,
        "surge_pct": surge * 100,
        "return_load_count": backhaul_count,
        "return_load_pct": backhaul * 100,
        "backhaul_poor_pct": poor * 100,
        "material_pct": material * 100,
        "fuel_index_pct": fuel_adj * 100,
        "extra_stops": int(load.extra_stops),
        "multi_drop_fee": rupee(multi_drop_fee),
        "total_adjustment_pct": total_pct * 100,
        "recommended_price": recommended,
    }
    return load.price

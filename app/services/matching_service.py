"""Truck eligibility filtering, HOS compliance, and ranking (BR-09..BR-13, BR-26, BR-28)."""

from decimal import Decimal

from config import (
    AVG_SPEED_KMPH,
    DAILY_HOS_LIMIT_HOURS,
    ELIGIBLE_TRUCK_RADIUS_KM,
    MIN_ELIGIBLE_RATING,
    ORIGIN_BUFFER_HOURS,
    TRIP_OVERHEAD_HOURS,
    TYPE_ORDER,
)
from app.models.entities import Carrier, Load, Truck
from app.services.exceptions import RuleError, lane_km


def evaluate_truck_eligibility(
    load: Load,
    truck: Truck,
    carrier: Carrier | None,
    distances: dict[tuple[str, str], int | float | Decimal],
) -> tuple[list[str], Decimal | None]:
    """Return rejection reasons (empty if eligible) and truck-to-origin distance."""
    reasons: list[str] = []

    if not truck.active or not carrier or not carrier.active:
        reasons.append("inactive")
    if carrier and carrier.rating < MIN_ELIGIBLE_RATING:
        reasons.append("rating below 3.0")
    if truck.capacity_tonnes < load.weight_tonnes:
        reasons.append("capacity")

    try:
        req_idx = TYPE_ORDER.index(load.truck_type)
        actual_idx = TYPE_ORDER.index(truck.truck_type)
        if actual_idx < req_idx or actual_idx > req_idx + 1:
            reasons.append("truck type")
    except ValueError:
        reasons.append("truck type")

    if truck.available_from > load.pickup_end:
        reasons.append("availability")

    km_to_origin: Decimal | None = None
    try:
        km_to_origin = lane_km(distances, truck.city, load.origin)
    except RuleError:
        reasons.append("unknown truck-origin distance")

    if km_to_origin is not None and km_to_origin > ELIGIBLE_TRUCK_RADIUS_KM:
        reasons.append("more than 150 km from origin")

    if load.material == "HAZARDOUS" and not truck.haz_certified:
        reasons.append("HAZ certification")
    if load.material == "OVERSIZE" and load.length_ft > truck.length_ft:
        reasons.append("oversize length")

    if km_to_origin is not None:
        travel_to_origin = km_to_origin / AVG_SPEED_KMPH
        remaining_hours = DAILY_HOS_LIMIT_HOURS - truck.hours_used
        second_driver = carrier.second_driver if carrier else False

        if remaining_hours < (travel_to_origin + ORIGIN_BUFFER_HOURS) and not second_driver:
            reasons.append("insufficient hours for travel to origin plus 2-hour buffer")

        try:
            trip_km = lane_km(distances, load.origin, load.destination)
            estimated_trip_hours = (trip_km / AVG_SPEED_KMPH) + TRIP_OVERHEAD_HOURS
            if remaining_hours < estimated_trip_hours and not second_driver:
                reasons.append("trip would breach 14-hour daily limit")
        except RuleError:
            reasons.append("unknown trip distance")

    return reasons, km_to_origin


def eligible_trucks(
    load: Load,
    trucks: list[Truck],
    carriers: dict[str, Carrier],
    distances: dict[tuple[str, str], int | float | Decimal],
    now: int = 0,
) -> tuple[list[Truck], dict[str, list[str]]]:
    """Filter eligible trucks and rank by distance asc, rating desc, truck_id asc (BR-13)."""
    _ = now
    ranked_rows: list[tuple[Truck, Decimal, Decimal]] = []
    rejected: dict[str, list[str]] = {}

    for truck in trucks:
        carrier = carriers.get(truck.carrier_id)
        reasons, km_to_origin = evaluate_truck_eligibility(load, truck, carrier, distances)
        if reasons:
            rejected[truck.id] = reasons
        else:
            assert km_to_origin is not None and carrier is not None
            ranked_rows.append((truck, km_to_origin, carrier.rating))

    ranked_rows.sort(key=lambda row: (row[1], -row[2], row[0].id))
    return [row[0] for row in ranked_rows], rejected

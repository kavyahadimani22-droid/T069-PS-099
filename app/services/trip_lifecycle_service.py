"""Detention, cancellation fees, and carrier rating lifecycle rules (BR-17..BR-21, BR-27)."""

from decimal import Decimal, ROUND_CEILING

from config import (
    DETENTION_RATES,
    FREE_DETENTION_HOURS,
    MAX_CARRIER_RATING,
    MAX_DETENTION_HOURS,
    MIN_CARRIER_RATING,
    SHIPPER_FREE_CANCEL_MINUTES,
    SHIPPER_MID_CANCEL_FEE,
    SHIPPER_MID_CANCEL_MINUTES,
)
from app.models.entities import Carrier
from app.services.exceptions import D, RuleError


RATING_DELTAS = {
    "ON_TIME": Decimal("0.05"),
    "LATE_OVER_4H": Decimal("-0.1"),
    "CANCELLED": Decimal("-0.2"),
}


def detention(hours: Decimal | int | float, truck_type: str) -> tuple[Decimal, int]:
    """Calculate capped detention charge and billable hours after 6 free hours (BR-17, BR-18)."""
    if truck_type not in DETENTION_RATES:
        raise RuleError(f"Unsupported truck type for detention: {truck_type}")
    excess = max(Decimal("0"), D(hours) - FREE_DETENTION_HOURS)
    rounded_hours = int(excess.to_integral_value(rounding=ROUND_CEILING))
    billable_hours = min(rounded_hours, MAX_DETENTION_HOURS)
    return D(billable_hours) * DETENTION_RATES[truck_type], billable_hours


def cancellation_fee(elapsed_minutes: int, base_price: Decimal | int | float) -> Decimal:
    """Calculate shipper cancellation fee based on elapsed minutes since match (BR-20)."""
    if elapsed_minutes <= SHIPPER_FREE_CANCEL_MINUTES:
        return Decimal("0")
    if elapsed_minutes <= SHIPPER_MID_CANCEL_MINUTES:
        return SHIPPER_MID_CANCEL_FEE
    return D(base_price) * Decimal("0.10")


def update_rating(carrier: Carrier, result: str) -> Decimal:
    """Update and clamp carrier rating between 1.0 and 5.0 (BR-27)."""
    if result not in RATING_DELTAS:
        raise RuleError(f"Unsupported rating event: {result}")
    carrier.rating = min(
        MAX_CARRIER_RATING,
        max(MIN_CARRIER_RATING, carrier.rating + RATING_DELTAS[result]),
    )
    return carrier.rating

"""Carrier counter-offer and shipper decision rules (BR-15 and BR-16)."""

from decimal import Decimal

from config import SHIPPER_COUNTER_WINDOW_MINUTES
from app.services.exceptions import D


def counter_status(recommended: Decimal | int | float, counter_amount: Decimal | int | float, elapsed: int) -> str:
    """Evaluate a carrier counter-offer against recommended freight price (BR-15, BR-16)."""
    rec = D(recommended)
    counter = D(counter_amount)
    pct = (counter - rec) / rec if rec else Decimal("0")

    if pct > Decimal("0.15"):
        return "REJECTED"
    if pct <= Decimal("0.05"):
        return "AUTO_ACCEPTED"
    if elapsed > SHIPPER_COUNTER_WINDOW_MINUTES:
        return "LAPSED"
    return "SHIPPER_DECISION_REQUIRED"

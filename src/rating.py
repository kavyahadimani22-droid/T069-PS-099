from decimal import Decimal
from config import RATING_MIN, RATING_MAX

def update_rating(carrier, outcome):
    changes = {"ON_TIME": Decimal("0.05"), "LATE_OVER_4H": Decimal("-0.1"), "CANCELLED": Decimal("-0.2")}
    if outcome not in changes:
        raise ValueError(f"Unknown rating outcome: {outcome}")
    carrier.rating = min(RATING_MAX, max(RATING_MIN, carrier.rating + changes[outcome]))
    return carrier.rating

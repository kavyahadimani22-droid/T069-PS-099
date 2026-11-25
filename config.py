"""Configuration constants and pricing/rule thresholds for T069-PS-099."""

from decimal import Decimal

# BR-01: Per-km freight rates (INR) by requested truck type
RATES: dict[str, Decimal] = {
    "LCV": Decimal("18"),
    "17FT": Decimal("24"),
    "22FT": Decimal("32"),
    "32FT_MXL": Decimal("45"),
    "TRAILER": Decimal("60"),
}

# BR-18: Hourly detention rates (INR) after 6 free hours, capped at 48 chargeable hours
DETENTION_RATES: dict[str, Decimal] = {
    "LCV": Decimal("300"),
    "17FT": Decimal("500"),
    "22FT": Decimal("500"),
    "32FT_MXL": Decimal("800"),
    "TRAILER": Decimal("800"),
}

# BR-10: Ordered truck categories (exact or one size larger allowed)
TYPE_ORDER: list[str] = ["LCV", "17FT", "22FT", "32FT_MXL", "TRAILER"]

# BR-01: Minimum chargeable distance in km
MIN_KM: Decimal = Decimal("150")

# BR-03 & BR-11: Distance radii (km)
SURGE_SUPPLY_RADIUS_KM: Decimal = Decimal("200")
RETURN_LOAD_RADIUS_KM: Decimal = Decimal("300")
ELIGIBLE_TRUCK_RADIUS_KM: Decimal = Decimal("150")

# BR-12 & BR-26: Driver Hours of Service (HOS) constants
DAILY_HOS_LIMIT_HOURS: Decimal = Decimal("14")
AVG_SPEED_KMPH: Decimal = Decimal("40")
ORIGIN_BUFFER_HOURS: Decimal = Decimal("2")
TRIP_OVERHEAD_HOURS: Decimal = Decimal("1")

# BR-14 & BR-16: Bidding and offer timers (minutes)
OFFER_EXPIRY_MINUTES: int = 30
SHIPPER_COUNTER_WINDOW_MINUTES: int = 60

# BR-17 & BR-18: Detention constants
FREE_DETENTION_HOURS: Decimal = Decimal("6")
MAX_DETENTION_HOURS: int = 48
ABORT_THRESHOLD_HOURS: Decimal = Decimal("48")

# BR-20 & BR-21: Cancellation constants
SHIPPER_FREE_CANCEL_MINUTES: int = 60
SHIPPER_MID_CANCEL_MINUTES: int = 360
SHIPPER_MID_CANCEL_FEE: Decimal = Decimal("1000")
CARRIER_CANCEL_FEE: Decimal = Decimal("2000")

# BR-22..BR-25: Settlement, GST, Platform Fee, and TDS constants
TOLL_CAP_MULTIPLIER: Decimal = Decimal("1.10")
PLATFORM_FEE_RATE: Decimal = Decimal("0.06")
GST_RATE: Decimal = Decimal("0.05")
TDS_RATE: Decimal = Decimal("0.01")
TDS_TRIP_THRESHOLD: Decimal = Decimal("30000")
TDS_ANNUAL_THRESHOLD: Decimal = Decimal("100000")

# BR-27 & BR-28: Carrier rating bounds and thresholds
DEFAULT_CARRIER_RATING: Decimal = Decimal("4.0")
MIN_CARRIER_RATING: Decimal = Decimal("1.0")
MAX_CARRIER_RATING: Decimal = Decimal("5.0")
MIN_ELIGIBLE_RATING: Decimal = Decimal("3.0")

# BR-29 & BR-30: Optional stretch-goal defaults (disabled at baseline)
DEFAULT_EXTRA_STOP_FEE: Decimal = Decimal("500")
DEFAULT_FUEL_INDEX_PCT: Decimal = Decimal("0")

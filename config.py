"""Central configuration. Currency is INR; all monetary outputs are rounded to whole rupees."""
from decimal import Decimal

CURRENCY = "INR"
RATES_PER_KM = {
    "LCV": Decimal("18"), "17FT": Decimal("24"), "22FT": Decimal("32"),
    "32FT_MXL": Decimal("45"), "TRAILER": Decimal("60"),
}
DETENTION_PER_HOUR = {
    "LCV": Decimal("300"), "17FT": Decimal("500"), "22FT": Decimal("500"),
    "32FT_MXL": Decimal("800"), "TRAILER": Decimal("800"),
}
MIN_CHARGEABLE_KM = 150
SURGE_BANDS = ((Decimal("4"), Decimal("0.30")), (Decimal("2.5"), Decimal("0.20")),
               (Decimal("1.5"), Decimal("0.10")))
LOW_DEMAND_THRESHOLD = Decimal("0.5")
LOW_DEMAND_ADJUSTMENT = Decimal("-0.10")
RETURN_LOAD_THRESHOLD = 3
RETURN_LOAD_RADIUS_KM = 300
RETURN_LOAD_DISCOUNT = Decimal("-0.08")
BACKHAUL_POOR_PREMIUM = Decimal("0.12")
HAZARDOUS_PREMIUM = Decimal("0.15")
PERISHABLE_PREMIUM = Decimal("0.10")
PLATFORM_FEE_RATE = Decimal("0.06")
GST_RATE = Decimal("0.05")
TDS_RATE = Decimal("0.01")
TDS_TRIP_THRESHOLD = Decimal("30000")
TDS_YEAR_THRESHOLD = Decimal("100000")
MAX_COUNTER_RATE = Decimal("0.15")
AUTO_ACCEPT_COUNTER_RATE = Decimal("0.05")
OFFER_RESPONSE_MINUTES = 30
COUNTER_RESPONSE_MINUTES = 60
FREE_DETENTION_HOURS = 6
MAX_DETENTION_HOURS = 48
DRIVER_DAILY_LIMIT_HOURS = Decimal("14")
SAFETY_BUFFER_HOURS = Decimal("2")
SPEED_KMPH = Decimal("40")
RATING_MIN = Decimal("1.0")
RATING_MAX = Decimal("5.0")

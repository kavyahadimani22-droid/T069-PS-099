"""Trip financial settlement, toll cap, GST, RCM, and TDS rules (BR-22 through BR-25)."""

from decimal import Decimal

from config import (
    GST_RATE,
    PLATFORM_FEE_RATE,
    TDS_ANNUAL_THRESHOLD,
    TDS_RATE,
    TDS_TRIP_THRESHOLD,
    TOLL_CAP_MULTIPLIER,
)
from app.models.entities import Carrier, Load, Shipper, Trip
from app.services.exceptions import D, rupee
from app.services.trip_lifecycle_service import detention


def settle(
    trip: Trip,
    load: Load,
    truck,
    carrier: Carrier,
    shipper: Shipper,
    lane_toll_cap: Decimal | int | float | None = None,
) -> dict:
    """Calculate carrier receipt and shipper invoice for a delivered trip (BR-22..BR-25)."""
    _ = load
    base = D(trip.base_price)
    freight = D(trip.agreed_price)
    pdet, pdet_hours = detention(trip.pickup_detention, truck.truck_type)
    ddet, ddet_hours = detention(trip.delivery_detention, truck.truck_type)

    toll = D(trip.toll_actual)
    if lane_toll_cap is not None:
        toll = min(toll, D(lane_toll_cap) * TOLL_CAP_MULTIPLIER)

    detention_total = pdet + ddet
    platform = rupee(base * PLATFORM_FEE_RATE)
    gross = freight + detention_total + toll
    before_tds = gross - platform

    # BR-25: Strict > thresholds; trip crossing annual ₹1,00,000 threshold triggers TDS
    crosses_year = (
        carrier.annual_payout <= TDS_ANNUAL_THRESHOLD
        and (carrier.annual_payout + before_tds) > TDS_ANNUAL_THRESHOLD
    )
    tds_due = (
        before_tds > TDS_TRIP_THRESHOLD
        or (carrier.annual_payout + before_tds) > TDS_ANNUAL_THRESHOLD
        or crosses_year
    )
    tds = rupee(before_tds * TDS_RATE) if tds_due else Decimal("0")
    payout = before_tds - tds
    carrier.annual_payout += payout

    # BR-24: 5% GST on freight; RCM flag when shipper is GST-registered
    gst = rupee(freight * GST_RATE)
    invoice = freight + detention_total + toll + gst

    return {
        "base_price": rupee(base),
        "freight": rupee(freight),
        "surge_and_other_adjustments": rupee(freight - base),
        "pickup_detention_hours": pdet_hours,
        "delivery_detention_hours": ddet_hours,
        "pickup_detention": rupee(pdet),
        "delivery_detention": rupee(ddet),
        "detention_total": rupee(detention_total),
        "toll": rupee(toll),
        "platform_fee": rupee(platform),
        "carrier_gross": rupee(gross),
        "tds": rupee(tds),
        "carrier_payout": rupee(payout),
        "gst": rupee(gst),
        "shipper_invoice": rupee(invoice),
        "rcm_flag": shipper.gst_registered,
    }

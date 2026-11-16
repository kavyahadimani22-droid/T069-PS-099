from decimal import Decimal, ROUND_HALF_UP
from config import *

def rupees(value):
    return Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

def detention_charge(hours, truck_type):
    hours = Decimal(hours)
    chargeable = max(Decimal("0"), hours - FREE_DETENTION_HOURS)
    rounded_hours = int(chargeable.to_integral_value(rounding="ROUND_CEILING"))
    capped_hours = min(rounded_hours, MAX_DETENTION_HOURS)
    return Decimal(capped_hours) * DETENTION_PER_HOUR[truck_type], capped_hours

def settle_trip(trip, load, truck, carrier, shipper, annual_payout_before):
    base = Decimal(trip.base_price)
    agreed = Decimal(trip.agreed_price)
    # Agreed carrier freight is used as the freight amount; retain price adjustment versus base.
    freight = agreed
    pickup_det, pickup_hours = detention_charge(trip.pickup_detention_hours, truck.truck_type)
    delivery_det, delivery_hours = detention_charge(trip.delivery_detention_hours, truck.truck_type)
    detention = pickup_det + delivery_det
    toll_cap = Decimal(str(load.price_breakdown.get("lane_toll_cap", trip.toll_actual)))
    toll = min(Decimal(trip.toll_actual), toll_cap * Decimal("1.10")) if toll_cap else Decimal(trip.toll_actual)
    platform_fee = rupees(base * PLATFORM_FEE_RATE)
    carrier_gross = freight + detention + toll
    carrier_net_before_tds = carrier_gross - platform_fee
    annual_after = Decimal(annual_payout_before) + carrier_net_before_tds
    tds_applies = carrier_net_before_tds > TDS_TRIP_THRESHOLD or annual_after > TDS_YEAR_THRESHOLD
    tds = rupees(carrier_net_before_tds * TDS_RATE) if tds_applies else Decimal("0")
    carrier_payout = carrier_net_before_tds - tds
    # Freight GST is 5%; toll/detention are invoiced separately without GST under this spec.
    gst = rupees(freight * GST_RATE)
    shipper_invoice = freight + detention + toll + gst
    carrier.annual_payout = annual_after
    trip.settlement = {
        "freight": rupees(freight), "base_price": rupees(base),
        "surge_and_price_adjustments": rupees(freight - base),
        "pickup_detention": rupees(pickup_det), "delivery_detention": rupees(delivery_det),
        "detention_total": rupees(detention), "toll_actual": rupees(toll),
        "platform_fee": rupees(platform_fee), "carrier_gross": rupees(carrier_gross),
        "tds": rupees(tds), "carrier_payout": rupees(carrier_payout),
        "gst": rupees(gst), "shipper_invoice": rupees(shipper_invoice),
        "rcm_flag": bool(shipper.gst_registered), "pickup_chargeable_hours": pickup_hours,
        "delivery_chargeable_hours": delivery_hours,
    }
    return trip.settlement

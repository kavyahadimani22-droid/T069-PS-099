from decimal import Decimal
from .utils import dec,cash,ceil_int
DETENTION_RATES={"LCV":300,"17FT":500,"22FT":500,"32FT_MXL":800,"TRAILER":800}
def detention_hours(wait):
    return max(0,ceil_int(max(Decimal(0),dec(wait)-6)))
def detention_charge(kind,pickup,delivery):
    if kind not in DETENTION_RATES:raise ValueError("Unknown truck type")
    return cash(min(48,detention_hours(pickup)+detention_hours(delivery))*DETENTION_RATES[kind])
def detention_abort_required(pickup,delivery):
    return detention_hours(pickup)+detention_hours(delivery)>48
def cancellation_charge(role,hours,base,carrier_reached_pickup=False):
    if role=="carrier":return Decimal("2000.00")
    if carrier_reached_pickup:return cash(dec(base)*Decimal(".10"))
    h=dec(hours)
    if h<=1:return Decimal("0.00")
    if h<=6:return Decimal("1000.00")
    return cash(dec(base)*Decimal(".10"))
def toll_charge(actual,cap):return cash(min(dec(actual),dec(cap)*Decimal("1.10")))
def tds_amount(payout,annual_before):
    p,a=dec(payout),dec(annual_before)
    return cash(p*Decimal(".01")) if p>30000 or a+p>100000 else Decimal("0.00")
def settle(base,kind,toll_actual=0,lane_cap=0,pickup_wait=0,delivery_wait=0,annual_payout=0,shipper_registered=False,surge_adjustment=0):
    b=cash(dec(base)+dec(surge_adjustment));toll=toll_charge(toll_actual,lane_cap);det=detention_charge(kind,pickup_wait,delivery_wait)
    fee=cash(dec(base)*Decimal(".06"));gst=cash(b*Decimal(".05"));gross=cash(b+toll+det);tds=tds_amount(gross,annual_payout)
    return {"base":cash(base),"surge_adjustment":cash(surge_adjustment),"platform_fee":fee,"toll":toll,"detention":det,"gst":gst,"rcm_flag":bool(shipper_registered),"carrier_gross":gross,"tds":tds,"carrier_net":cash(gross-fee-tds),"shipper_invoice":cash(b+fee+toll+det+gst)}

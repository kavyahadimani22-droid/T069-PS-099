from decimal import Decimal, ROUND_HALF_UP, ROUND_CEILING
from config import RATES, DETENTION_RATES, TYPE_ORDER, MIN_KM
from src.models import State

class RuleError(ValueError): pass

def D(v): return Decimal(str(v))
def rupee(v): return D(v).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

def lane_km(distances, a, b):
    if a == b: return Decimal("0")
    if (a,b) in distances: return D(distances[(a,b)])
    if (b,a) in distances: return D(distances[(b,a)])
    raise RuleError(f"Unknown city pair: {a} -> {b}")

def validate_load(load):
    if load.weight_tonnes <= 0: raise RuleError("Load weight must be positive")
    if load.truck_type not in RATES: raise RuleError("Unsupported truck type")
    if load.pickup_end < load.pickup_start: raise RuleError("Invalid pickup window")
    if load.material not in {"GENERAL","HAZARDOUS","PERISHABLE","OVERSIZE"}: raise RuleError("Invalid material class")
    if load.material == "PERISHABLE" and load.pickup_end-load.pickup_start > 360:
        raise RuleError("Perishable pickup window must be at most 6 hours")

def price_load(load, trucks, loads, distances, poor_cities):
    validate_load(load)
    km = lane_km(distances, load.origin, load.destination)
    charge_km = max(km, MIN_KM)
    base = charge_km * RATES[load.truck_type]
    available = []
    for t in trucks:
        if t.active and t.truck_type == load.truck_type:
            try:
                if lane_km(distances, t.city, load.origin) <= 200: available.append(t)
            except RuleError: pass
    demand = sum(1 for x in loads if x.open and x.origin == load.origin and x.truck_type == load.truck_type)
    ratio = D(demand)/D(len(available)) if available else (D("999999") if demand else D("0"))
    surge = D("0")
    if ratio > 4: surge=D(".30")
    elif ratio > D("2.5"): surge=D(".20")
    elif ratio > D("1.5"): surge=D(".10")
    elif ratio < D(".5"): surge=D("-.10")
    backhaul_count=0
    for x in loads:
        if x.id == load.id or not x.open or x.origin != load.destination or x.truck_type != load.truck_type: continue
        try:
            if lane_km(distances, x.destination, load.origin) <= 300: backhaul_count += 1
        except RuleError: pass
    backhaul = D("-.08") if backhaul_count >= 3 else D("0")
    poor = D(".12") if load.destination in poor_cities else D("0")
    material = {"HAZARDOUS":D(".15"),"PERISHABLE":D(".10")}.get(load.material,D("0"))
    total = surge + backhaul + poor + material
    recommended = rupee(base*(1+total))
    load.recommended = recommended
    load.price = {"distance_km":km,"chargeable_km":charge_km,"rate_per_km":RATES[load.truck_type],
      "base_price":rupee(base),"open_loads":demand,"available_trucks_200km":len(available),
      "demand_supply_ratio":ratio,"surge_pct":surge*100,"return_load_count":backhaul_count,
      "return_load_pct":backhaul*100,"backhaul_poor_pct":poor*100,"material_pct":material*100,
      "total_adjustment_pct":total*100,"recommended_price":recommended}
    return load.price

def eligible_trucks(load, trucks, carriers, distances, now=0):
    ok=[]; rejected={}
    for t in trucks:
        why=[]; c=carriers.get(t.carrier_id)
        if not t.active or not c or not c.active: why.append("inactive")
        if c and c.rating < 3: why.append("rating below 3.0")
        if t.capacity_tonnes < load.weight_tonnes: why.append("capacity")
        try:
            req=TYPE_ORDER.index(load.truck_type); actual=TYPE_ORDER.index(t.truck_type)
            if actual < req or actual > req+1: why.append("truck type")
        except ValueError: why.append("truck type")
        if t.available_from > load.pickup_end: why.append("availability")
        try: km=lane_km(distances,t.city,load.origin)
        except RuleError: km=None; why.append("unknown truck-origin distance")
        if km is not None and km > 150: why.append("more than 150 km from origin")
        if load.material=="HAZARDOUS" and not t.haz_certified: why.append("HAZ certification")
        if load.material=="OVERSIZE" and load.length_ft > t.length_ft: why.append("oversize length")
        if km is not None:
            travel_to_origin=km/D(40)
            remaining=D(14)-t.hours_used
            if remaining < travel_to_origin+D(2) and not c.second_driver:
                why.append("insufficient hours for travel to origin plus 2-hour buffer")
            try:
                trip_km=lane_km(distances,load.origin,load.destination)
                estimated_trip_hours=trip_km/D(40)+D(1)
                if remaining < estimated_trip_hours and not c.second_driver:
                    why.append("trip would breach 14-hour daily limit")
            except RuleError:
                why.append("unknown trip distance")
        if why: rejected[t.id]=why
        else: ok.append((t,km,c.rating))
    ok.sort(key=lambda x:(x[1],-x[2],x[0].id))
    return [x[0] for x in ok],rejected

def detention(hours, truck_type):
    excess=max(D(0),D(hours)-D(6))
    rounded=int(excess.to_integral_value(rounding=ROUND_CEILING))
    billable=min(rounded,48)
    return D(billable)*DETENTION_RATES[truck_type],billable

def counter_status(recommended, counter, elapsed):
    recommended=D(recommended); counter=D(counter)
    pct=(counter-recommended)/recommended if recommended else D(0)
    if pct > D(".15"): return "REJECTED"
    if pct <= D(".05"): return "AUTO_ACCEPTED"
    if elapsed > 60: return "LAPSED"
    return "SHIPPER_DECISION_REQUIRED"

def cancellation_fee(elapsed_minutes, base):
    if elapsed_minutes <= 60: return D(0)
    if elapsed_minutes <= 360: return D(1000)
    return D(base)*D(".10")

def update_rating(carrier, result):
    change={"ON_TIME":D(".05"),"LATE_OVER_4H":D("-.1"),"CANCELLED":D("-.2")}[result]
    carrier.rating=min(D(5),max(D(1),carrier.rating+change))
    return carrier.rating

def settle(trip, load, truck, carrier, shipper, lane_toll_cap=None):
    base=D(trip.base_price); freight=D(trip.agreed_price)
    pdet,_=detention(trip.pickup_detention,truck.truck_type)
    ddet,_=detention(trip.delivery_detention,truck.truck_type)
    toll=D(trip.toll_actual)
    if lane_toll_cap is not None: toll=min(toll,D(lane_toll_cap)*D("1.10"))
    detention_total=pdet+ddet
    platform=rupee(base*D(".06"))
    gross=freight+detention_total+toll
    before_tds=gross-platform
    # Cumulative threshold: tax applies to the trip that crosses annual 100k.
    crosses_year=(carrier.annual_payout <= D(100000) and carrier.annual_payout+before_tds > D(100000))
    tds_due=before_tds > D(30000) or carrier.annual_payout+before_tds > D(100000) or crosses_year
    tds=rupee(before_tds*D(".01")) if tds_due else D(0)
    payout=before_tds-tds
    carrier.annual_payout += payout
    gst=rupee(freight*D(".05"))
    invoice=freight+detention_total+toll+gst
    return {"base_price":rupee(base),"freight":rupee(freight),"surge_and_other_adjustments":rupee(freight-base),
      "pickup_detention":rupee(pdet),"delivery_detention":rupee(ddet),"detention_total":rupee(detention_total),
      "toll":rupee(toll),"platform_fee":rupee(platform),"carrier_gross":rupee(gross),
      "tds":rupee(tds),"carrier_payout":rupee(payout),"gst":rupee(gst),"shipper_invoice":rupee(invoice),
      "rcm_flag":shipper.gst_registered}

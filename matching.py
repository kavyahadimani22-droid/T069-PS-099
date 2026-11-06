from decimal import Decimal
from config import TYPES
from .utils import dec
from .pricing import distance
def trip_hours(km):return dec(km)/Decimal(40)+Decimal(1)
def eligible(m,l,t):
    c=m.carriers.get(t.carrier_id)
    if not t.active:return False,"inactive truck"
    if c is None or c.rating<3:return False,"carrier rating below 3"
    if t.capacity_tonnes<l.weight_tonnes:return False,"insufficient capacity"
    if t.truck_type not in TYPES or l.truck_type not in TYPES or TYPES.index(t.truck_type)<TYPES.index(l.truck_type):return False,"truck type incompatible"
    if l.material_class=="HAZARDOUS" and not t.haz_certified:return False,"HAZ certification required"
    if l.length_ft>t.length_ft:return False,"load exceeds truck length"
    if t.available_from>l.pickup_end:return False,"truck unavailable"
    try:approach=distance(m,t.current_city,l.origin);lane=distance(m,l.origin,l.destination)
    except ValueError:return False,"unknown distance pair"
    if approach>150:return False,"truck more than 150 km from origin"
    if not t.second_driver and Decimal(14)-t.driver_hours_used<trip_hours(approach)+2:return False,"insufficient driver hours including buffer"
    if l.material_class=="PERISHABLE" and (l.pickup_end-l.pickup_start).total_seconds()>21600:return False,"perishable window exceeds 6h"
    return True,"eligible"
def rank_trucks(m,l):
    candidates=[]
    for t in m.trucks.values():
        ok,_=eligible(m,l,t)
        if ok:candidates.append((distance(m,t.current_city,l.origin),-m.carriers[t.carrier_id].rating,t.truck_id,t))
    candidates.sort(key=lambda x:x[:3]);return [x[3] for x in candidates[:3]]
def run_matching_cycle(m,prices):
    from .models import Proposal
    result=[]
    for l in m.loads.values():
        p=prices.get(l.load_id)
        if l.open and p and p.status=="PRICED":
            for rank,t in enumerate(rank_trucks(m,l),1):
                result.append(Proposal(l.load_id,t.truck_id,t.carrier_id,distance(m,t.current_city,l.origin),p.recommended,rank))
    return result

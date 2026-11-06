from decimal import Decimal
from config import MIN_KM,RATES
from .models import Price
from .utils import dec,cash
def distance(m,a,b):
    if a==b:return Decimal(0)
    if (a,b) not in m.distances: raise ValueError(f"REJECTED: unknown distance pair {a}->{b}")
    return dec(m.distances[a,b])
def surge_rate(r):
    r=dec(r)
    if r>4:return Decimal(".30")
    if r>Decimal("2.5"):return Decimal(".20")
    if r>Decimal("1.5"):return Decimal(".10")
    if r<Decimal(".5"):return Decimal("-.10")
    return Decimal(0)
def near(m,a,b,radius):
    try:return distance(m,a,b)<=Decimal(radius)
    except ValueError:return False
def calculate_price(m,l,open_loads=None,available_trucks=None):
    km=distance(m,l.origin,l.destination); charge=max(km,MIN_KM)
    if l.truck_type not in RATES:raise ValueError("REJECTED: unknown truck type")
    base=cash(charge*RATES[l.truck_type])
    ol=open_loads if open_loads is not None else [x for x in m.loads.values() if x.open and x.truck_type==l.truck_type and near(m,l.origin,x.origin,200)]
    ts=available_trucks if available_trucks is not None else [t for t in m.trucks.values() if t.active and t.truck_type==l.truck_type and t.available_from<=l.pickup_end and near(m,l.origin,t.current_city,200)]
    ratio=Decimal(len(ol))/Decimal(len(ts)) if ts else (Decimal("Infinity") if ol else Decimal(0))
    sp=surge_rate(ratio)
    returns=sum(1 for x in m.loads.values() if x.open and x.load_id!=l.load_id and x.truck_type==l.truck_type and x.origin==l.destination and near(m,x.destination,l.origin,300))
    rp=Decimal(".08") if returns>=3 else Decimal(0)
    pp=Decimal(".12") if l.destination in m.backhaul_poor else Decimal(0)
    mat=l.material_class.upper()
    if mat not in {"GENERAL","HAZARDOUS","PERISHABLE","OVERSIZE"}:raise ValueError("REJECTED: unsupported material")
    window=(l.pickup_end-l.pickup_start).total_seconds()/3600
    if mat=="PERISHABLE" and window>6:raise ValueError("REJECTED: perishable window exceeds 6h")
    if mat=="OVERSIZE" and l.length_ft<=0:raise ValueError("REJECTED: oversize length missing")
    mp=Decimal(".15") if mat=="HAZARDOUS" else Decimal(".10") if mat=="PERISHABLE" else Decimal(0)
    surge=cash(base*sp);ret=cash(base*rp);poor=cash(base*pp);material=cash(base*mp)
    return Price(l.load_id,km,charge,base,sp,surge,rp,ret,pp,poor,mp,material,cash(base+surge-ret+poor+material))
def price_all_loads(m):
    out={}
    for l in m.loads.values():
        try:out[l.load_id]=calculate_price(m,l)
        except ValueError as e:out[l.load_id]=Price(l.load_id,0,0,0,0,0,0,0,0,0,0,0,0,"REJECTED",str(e))
    return out

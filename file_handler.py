import csv
from pathlib import Path
from dataclasses import dataclass,field
from .models import Carrier,Shipper,Truck,Load
from .utils import dec,dt
@dataclass
class Market:
    carriers:dict=field(default_factory=dict); shippers:dict=field(default_factory=dict)
    trucks:dict=field(default_factory=dict); loads:dict=field(default_factory=dict)
    distances:dict=field(default_factory=dict); toll_caps:dict=field(default_factory=dict)
    toll_actual:dict=field(default_factory=dict); backhaul_poor:set=field(default_factory=set)
    trips:dict=field(default_factory=dict); offers:dict=field(default_factory=dict)
def rows(path):
    if not Path(path).exists(): return []
    with open(path,newline="",encoding="utf-8-sig") as f: return list(csv.DictReader(f))
def flag(v): return str(v).lower() in {"1","true","yes","y"}
def load_market(folder):
    folder=Path(folder); m=Market()
    for r in rows(folder/"carriers.csv"):
        x=Carrier(r["carrier_id"],r.get("name",""),dec(r.get("rating") or 4),flag(r.get("registered")),dec(r.get("cumulative_payout_year")))
        m.carriers[x.carrier_id]=x
    for r in rows(folder/"shippers.csv"):
        x=Shipper(r["shipper_id"],r.get("name",""),flag(r.get("gst_registered")));m.shippers[x.shipper_id]=x
    for r in rows(folder/"trucks.csv"):
        x=Truck(r["truck_id"],r["carrier_id"],r["truck_type"].upper(),dec(r["capacity_tonnes"]),dec(r["length_ft"]),r["current_city"],dt(r["available_from"]),dec(r.get("driver_hours_used")),flag(r.get("haz_certified")),flag(r.get("second_driver")),r.get("active","true").lower() not in {"false","0","no"})
        m.trucks[x.truck_id]=x
    for r in rows(folder/"loads.csv"):
        x=Load(r["load_id"],r["shipper_id"],r["origin"],r["destination"],dec(r["weight_tonnes"]),r["truck_type"].upper(),dt(r["pickup_start"]),dt(r["pickup_end"]),r.get("material_class","GENERAL").upper(),dec(r.get("length_ft")),r.get("open","true").lower() not in {"false","0","no"})
        m.loads[x.load_id]=x
    for r in rows(folder/"distances.csv"):
        a,b,k=r["origin"],r["destination"],dec(r["distance_km"]);m.distances[a,b]=k;m.distances[b,a]=k
    for r in rows(folder/"tolls.csv"):
        k=(r["origin"],r["destination"]);m.toll_caps[k]=dec(r.get("lane_toll_cap"));m.toll_actual[k]=dec(r.get("actual_toll"))
    for r in rows(folder/"backhaul_poor.csv"):
        c=r.get("city") or r.get("destination")
        if c:m.backhaul_poor.add(c)
    return m

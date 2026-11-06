import csv
from dataclasses import asdict
def write_rows(rows,path,fields):
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def write_price_report(prices,path):
    fields=list(next(iter(prices.values())).__dataclass_fields__) if prices else ["load_id"]
    write_rows([{k:str(v) for k,v in asdict(p).items()} for p in prices.values()],path,fields)
def write_matching_log(proposals,path):
    fields=["load_id","truck_id","carrier_id","distance_km","recommended","rank"]
    write_rows([{k:str(getattr(p,k)) for k in fields} for p in proposals],path,fields)
def write_settlements(trips,path):
    fields=["trip_id","load_id","state","base","surge_adjustment","platform_fee","toll","detention","gst","rcm_flag","carrier_gross","tds","carrier_net","shipper_invoice"]
    rows=[]
    for t in trips.values():
        d={"trip_id":t.trip_id,"load_id":t.load_id,"state":t.state.value};d.update(t.settled);rows.append({k:str(d.get(k,"")) for k in fields})
    write_rows(rows,path,fields)

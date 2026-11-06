from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
class State(str,Enum):
    MATCHED="MATCHED"; AT_PICKUP="AT_PICKUP"; LOADED="LOADED"
    IN_TRANSIT="IN_TRANSIT"; DELIVERED="DELIVERED"; SETTLED="SETTLED"
    CANCELLED="CANCELLED"; ABORTED="ABORTED"
@dataclass
class Carrier:
    carrier_id:str; name:str=""; rating:Decimal=Decimal("4.0")
    registered:bool=False; cumulative_payout_year:Decimal=Decimal("0")
@dataclass
class Shipper:
    shipper_id:str; name:str=""; gst_registered:bool=False
@dataclass
class Truck:
    truck_id:str; carrier_id:str; truck_type:str; capacity_tonnes:Decimal
    length_ft:Decimal; current_city:str; available_from:datetime
    driver_hours_used:Decimal=Decimal("0"); haz_certified:bool=False
    second_driver:bool=False; active:bool=True
@dataclass
class Load:
    load_id:str; shipper_id:str; origin:str; destination:str
    weight_tonnes:Decimal; truck_type:str; pickup_start:datetime; pickup_end:datetime
    material_class:str="GENERAL"; length_ft:Decimal=Decimal("0"); open:bool=True
@dataclass
class Price:
    load_id:str; distance_km:Decimal; chargeable_km:Decimal; base:Decimal
    surge_pct:Decimal; surge:Decimal; return_pct:Decimal; return_discount:Decimal
    poor_pct:Decimal; poor:Decimal; material_pct:Decimal; material:Decimal
    recommended:Decimal; status:str="PRICED"; reason:str=""
@dataclass
class Proposal:
    load_id:str; truck_id:str; carrier_id:str; distance_km:Decimal
    recommended:Decimal; rank:int
@dataclass
class Trip:
    trip_id:str; load_id:str; truck_id:str; carrier_id:str; shipper_id:str
    base:Decimal; matched_at:datetime; state:State=State.MATCHED
    accepted_price:Decimal=Decimal("0"); pickup_wait_hours:Decimal=Decimal("0")
    delivery_wait_hours:Decimal=Decimal("0"); toll_actual:Decimal=Decimal("0")
    second_driver:bool=False; cancellation_charge:Decimal=Decimal("0")
    settled:dict=field(default_factory=dict)

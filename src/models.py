from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum

class State(str, Enum):
    MATCHED="MATCHED"; AT_PICKUP="AT_PICKUP"; LOADED="LOADED"
    IN_TRANSIT="IN_TRANSIT"; DELIVERED="DELIVERED"; SETTLED="SETTLED"
    CANCELLED="CANCELLED"; ABORTED="ABORTED"

@dataclass
class Shipper:
    id: str
    name: str
    gst_registered: bool=False

@dataclass
class Carrier:
    id: str
    name: str
    rating: Decimal=Decimal("4.0")
    annual_payout: Decimal=Decimal("0")
    second_driver: bool=False
    active: bool=True

@dataclass
class Truck:
    id: str
    carrier_id: str
    truck_type: str
    capacity_tonnes: Decimal
    length_ft: Decimal
    city: str
    available_from: int=0
    hours_used: Decimal=Decimal("0")
    haz_certified: bool=False
    active: bool=True

@dataclass
class Load:
    id: str
    shipper_id: str
    origin: str
    destination: str
    weight_tonnes: Decimal
    truck_type: str
    pickup_start: int
    pickup_end: int
    material: str="GENERAL"
    length_ft: Decimal=Decimal("0")
    open: bool=True
    price: dict=field(default_factory=dict)
    recommended: Decimal=Decimal("0")

@dataclass
class Trip:
    id: str
    load_id: str
    truck_id: str
    carrier_id: str
    shipper_id: str
    state: State
    matched_at: int
    agreed_price: Decimal
    base_price: Decimal
    offer_deadline: int
    accepted_at: int|None=None
    pickup_detention: Decimal=Decimal("0")
    delivery_detention: Decimal=Decimal("0")
    toll_actual: Decimal=Decimal("0")
    settlement: dict=field(default_factory=dict)
    cancel_fee: Decimal=Decimal("0")

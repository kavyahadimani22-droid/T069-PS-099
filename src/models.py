from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional

class TripState(str, Enum):
    MATCHED = "MATCHED"
    AT_PICKUP = "AT_PICKUP"
    LOADED = "LOADED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    SETTLED = "SETTLED"
    CANCELLED = "CANCELLED"
    ABORTED = "ABORTED"

@dataclass
class Shipper:
    shipper_id: str
    name: str
    gst_registered: bool = False

@dataclass
class Carrier:
    carrier_id: str
    name: str
    rating: Decimal = Decimal("4.0")
    annual_payout: Decimal = Decimal("0")
    second_driver: bool = False
    active: bool = True

@dataclass
class Truck:
    truck_id: str
    carrier_id: str
    truck_type: str
    capacity_tonnes: Decimal
    length_ft: Decimal
    current_city: str
    available_from: int
    driver_hours_used: Decimal = Decimal("0")
    haz_certified: bool = False
    active: bool = True

@dataclass
class Load:
    load_id: str
    shipper_id: str
    origin: str
    destination: str
    weight_tonnes: Decimal
    truck_type: str
    pickup_start: int
    pickup_end: int
    material_class: str = "GENERAL"
    length_ft: Decimal = Decimal("0")
    open: bool = True
    recommended_price: Decimal = Decimal("0")
    price_breakdown: dict = field(default_factory=dict)

@dataclass
class Bid:
    truck_id: str
    amount: Decimal
    created_at: int
    status: str = "PENDING"

@dataclass
class Trip:
    trip_id: str
    load_id: str
    truck_id: str
    carrier_id: str
    shipper_id: str
    state: TripState
    matched_at: int
    accepted_at: int
    agreed_price: Decimal
    base_price: Decimal
    events: list = field(default_factory=list)
    toll_actual: Decimal = Decimal("0")
    pickup_detention_hours: Decimal = Decimal("0")
    delivery_detention_hours: Decimal = Decimal("0")
    cancellation_fee: Decimal = Decimal("0")
    settlement: dict = field(default_factory=dict)

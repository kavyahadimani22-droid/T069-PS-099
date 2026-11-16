from decimal import Decimal
from config import RATES_PER_KM

class RuleViolation(ValueError):
    pass

def validate_city_pair(origin, destination, distances):
    if (origin, destination) not in distances and (destination, origin) not in distances:
        raise RuleViolation(f"Unknown distance pair: {origin} -> {destination}")

def distance_between(origin, destination, distances):
    validate_city_pair(origin, destination, distances)
    return Decimal(str(distances.get((origin, destination), distances.get((destination, origin)))))

def validate_load(load):
    if load.weight_tonnes <= 0:
        raise RuleViolation("Load weight must be positive")
    if load.truck_type not in RATES_PER_KM:
        raise RuleViolation(f"Unsupported truck type: {load.truck_type}")
    if load.pickup_end < load.pickup_start:
        raise RuleViolation("Pickup window end precedes start")
    if load.material_class not in {"GENERAL", "HAZARDOUS", "PERISHABLE", "OVERSIZE"}:
        raise RuleViolation(f"Unsupported material class: {load.material_class}")

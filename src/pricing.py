from decimal import Decimal, ROUND_HALF_UP
from config import *
from src.validation import distance_between, RuleViolation

def money(value):
    return Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

class PricingEngine:
    def __init__(self, distances, backhaul_poor_cities=None):
        self.distances = distances
        self.backhaul_poor_cities = set(backhaul_poor_cities or [])

    def calculate(self, load, trucks, loads):
        km = distance_between(load.origin, load.destination, self.distances)
        charge_km = max(km, Decimal(MIN_CHARGEABLE_KM))
        rate = RATES_PER_KM[load.truck_type]
        base = charge_km * rate

        # Supply count is unique active trucks positioned within 200 km of the origin.
        available = [t for t in trucks if t.active and t.truck_type == load.truck_type
                     and self._city_distance(t.current_city, load.origin) <= 200]
        open_loads = [x for x in loads if x.open and x.origin == load.origin
                      and x.truck_type == load.truck_type]
        ratio = Decimal(len(open_loads)) / Decimal(max(len(available), 1))
        if not available:
            ratio = Decimal("999") if open_loads else Decimal("0")

        surge = Decimal("0")
        for threshold, adjustment in SURGE_BANDS:
            if ratio > threshold:
                surge = adjustment
                break
        if ratio < LOW_DEMAND_THRESHOLD:
            surge = LOW_DEMAND_ADJUSTMENT

        # Return-load condition is measured at the destination city; nearby destination loads
        # are counted if their destination is within 300 km of the original load's origin.
        backhaul_count = 0
        for candidate in loads:
            if not candidate.open or candidate.load_id == load.load_id:
                continue
            if candidate.origin != load.destination or candidate.truck_type != load.truck_type:
                continue
            try:
                if self._city_distance(candidate.destination, load.origin) <= RETURN_LOAD_RADIUS_KM:
                    backhaul_count += 1
            except RuleViolation:
                continue
        return_factor = RETURN_LOAD_DISCOUNT if backhaul_count >= RETURN_LOAD_THRESHOLD else Decimal("0")
        poor_factor = BACKHAUL_POOR_PREMIUM if load.destination in self.backhaul_poor_cities else Decimal("0")
        material_factor = Decimal("0")
        if load.material_class == "HAZARDOUS":
            material_factor = HAZARDOUS_PREMIUM
        elif load.material_class == "PERISHABLE":
            material_factor = PERISHABLE_PREMIUM
            if load.pickup_end - load.pickup_start > 6 * 60:
                raise RuleViolation("Perishable load pickup window exceeds 6 hours")
        elif load.material_class == "OVERSIZE":
            # Truck-specific length is checked during eligibility; price can still be quoted.
            material_factor = Decimal("0")

        # Percent adjustments are additive on base, then rounded once to whole rupees.
        adjustment = surge + return_factor + poor_factor + material_factor
        recommended = money(base * (Decimal("1") + adjustment))
        result = {
            "distance_km": km, "chargeable_km": charge_km, "rate_per_km": rate,
            "base_price": money(base), "demand_supply_ratio": ratio,
            "surge_adjustment_pct": surge * 100, "return_load_count": backhaul_count,
            "return_load_adjustment_pct": return_factor * 100,
            "backhaul_poor_adjustment_pct": poor_factor * 100,
            "material_adjustment_pct": material_factor * 100,
            "total_adjustment_pct": adjustment * 100,
            "recommended_price": recommended,
        }
        load.recommended_price = recommended
        load.price_breakdown = result
        return result

    def _city_distance(self, a, b):
        if a == b:
            return Decimal("0")
        return distance_between(a, b, self.distances)

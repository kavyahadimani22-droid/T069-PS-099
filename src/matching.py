from decimal import Decimal
from config import *
from src.validation import distance_between, RuleViolation

class MatchingEngine:
    def __init__(self, distances, carriers):
        self.distances = distances
        self.carriers = carriers

    def eligible_trucks(self, load, trucks):
        eligible = []
        rejected = {}
        for truck in trucks:
            reasons = []
            carrier = self.carriers.get(truck.carrier_id)
            if not truck.active or carrier is None or not carrier.active:
                reasons.append("inactive truck/carrier")
            if carrier and carrier.rating < Decimal("3.0"):
                reasons.append("carrier rating below 3.0")
            if truck.capacity_tonnes < load.weight_tonnes:
                reasons.append("insufficient capacity")
            # One size larger is permitted, at the requested smaller truck's price.
            if not self._type_compatible(load.truck_type, truck.truck_type):
                reasons.append("truck type mismatch")
            if truck.available_from > load.pickup_end:
                reasons.append("truck unavailable before pickup window end")
            try:
                origin_km = distance_between(truck.current_city, load.origin, self.distances)
                if origin_km > 150:
                    reasons.append("truck more than 150 km from origin")
            except RuleViolation:
                origin_km = None
                reasons.append("unknown truck-to-origin distance")
            if load.material_class == "HAZARDOUS" and not truck.haz_certified:
                reasons.append("HAZ certification required")
            if load.material_class == "PERISHABLE" and load.pickup_end - load.pickup_start > 360:
                reasons.append("perishable pickup window exceeds 6 hours")
            if load.material_class == "OVERSIZE" and load.length_ft > truck.length_ft:
                reasons.append("oversize length exceeds truck length")
            if origin_km is not None:
                estimated_to_origin = origin_km / SPEED_KMPH
                remaining = DRIVER_DAILY_LIMIT_HOURS - truck.driver_hours_used
                required_to_origin = estimated_to_origin + SAFETY_BUFFER_HOURS
                # The HOS rule separately checks the estimated loaded trip duration.
                lane_km = distance_between(load.origin, load.destination, self.distances)
                estimated_trip_hours = lane_km / SPEED_KMPH + Decimal("1")
                second_driver = bool(carrier and carrier.second_driver)
                if remaining < required_to_origin and not second_driver:
                    reasons.append("insufficient driver hours including 2-hour buffer")
                if remaining < estimated_trip_hours and not second_driver:
                    reasons.append("trip would breach 14-hour daily driver limit")
            if reasons:
                rejected[truck.truck_id] = reasons
            else:
                eligible.append((truck, origin_km, carrier.rating))
        eligible.sort(key=lambda item: (item[1], -item[2], item[0].truck_id))
        return [x[0] for x in eligible], rejected

    @staticmethod
    def _type_compatible(requested, actual):
        order = ["LCV", "17FT", "22FT", "32FT_MXL", "TRAILER"]
        try:
            return order.index(actual) >= order.index(requested) and order.index(actual) - order.index(requested) <= 1
        except ValueError:
            return False

    def rank_and_offer(self, load, trucks):
        eligible, rejected = self.eligible_trucks(load, trucks)
        return eligible[:3], rejected

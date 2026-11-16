from decimal import Decimal
from src.models import *
from src.pricing import PricingEngine
from src.matching import MatchingEngine
from src.bidding import BiddingEngine
from src.settlement import settle_trip
from src.rating import update_rating
from src.validation import validate_load, RuleViolation

class FreightEngine:
    def __init__(self, distances, backhaul_poor_cities=None):
        self.distances = distances
        self.shippers, self.carriers, self.trucks, self.loads, self.trips = {}, {}, {}, {}, {}
        self.logs = []
        self.pricer = PricingEngine(distances, backhaul_poor_cities)
        self.matcher = MatchingEngine(distances, self.carriers)
        self.bids = BiddingEngine()
        self.current_minute = 0
        self.toll_table = {}

    def register_shipper(self, obj): self.shippers[obj.shipper_id] = obj
    def register_carrier(self, obj): self.carriers[obj.carrier_id] = obj
    def register_truck(self, obj):
        if obj.carrier_id not in self.carriers: raise RuleViolation("Truck carrier is not registered")
        self.trucks[obj.truck_id] = obj
    def post_load(self, obj):
        if obj.shipper_id not in self.shippers: raise RuleViolation("Load shipper is not registered")
        validate_load(obj)
        self.loads[obj.load_id] = obj
        return self.pricer.calculate(obj, list(self.trucks.values()), list(self.loads.values()))

    def run_matching_cycle(self):
        for load in sorted(self.loads.values(), key=lambda x: x.load_id):
            if not load.open: continue
            try:
                # Recalculate at every cycle using the live open-load and truck pool.
                self.pricer.calculate(load, list(self.trucks.values()), list(self.loads.values()))
                top, rejected = self.matcher.rank_and_offer(load, list(self.trucks.values()))
                self.logs.append(f"CYCLE {self.current_minute}: LOAD {load.load_id} recommended Rs {load.recommended_price}")
                for truck in top:
                    self.logs.append(f"  OFFER {load.load_id} -> {truck.truck_id} carrier={truck.carrier_id}")
                for truck_id, reasons in rejected.items():
                    self.logs.append(f"  REJECT {truck_id}: {', '.join(reasons)}")
                if top:
                    selected = top[0]
                    trip_id = f"TRIP-{load.load_id}"
                    trip = Trip(trip_id, load.load_id, selected.truck_id, selected.carrier_id,
                                load.shipper_id, TripState.MATCHED, self.current_minute,
                                self.current_minute, load.recommended_price, load.price_breakdown["base_price"])
                    self.trips[trip_id] = trip
                    load.open = False
                    self.logs.append(f"  MATCHED {trip_id} with {selected.truck_id}")
            except RuleViolation as exc:
                self.logs.append(f"  LOAD {load.load_id} REJECTED: {exc}")

    def submit_counter(self, trip_id, amount, elapsed_minutes=0):
        trip = self.trips[trip_id]
        result = self.bids.evaluate_counter(trip.agreed_price, Decimal(str(amount)), elapsed_minutes)
        self.logs.append(f"COUNTER {trip_id}: Rs {amount} -> {result}")
        if result == "AUTO_ACCEPTED":
            trip.agreed_price = Decimal(str(amount))
        return result

    def event(self, trip_id, event_name, **kwargs):
        trip = self.trips[trip_id]
        load = self.loads[trip.load_id]
        truck = self.trucks[trip.truck_id]
        carrier = self.carriers[trip.carrier_id]
        shipper = self.shippers[trip.shipper_id]
        allowed = {
            TripState.MATCHED: {"AT_PICKUP", "CANCEL_SHIPPER", "CANCEL_CARRIER", "NO_SHOW"},
            TripState.AT_PICKUP: {"LOADED", "CANCEL_CARRIER", "ABORT"},
            TripState.LOADED: {"IN_TRANSIT"},
            TripState.IN_TRANSIT: {"DELIVERED"},
            TripState.DELIVERED: {"SETTLE"},
        }
        if event_name not in allowed.get(trip.state, set()):
            raise RuleViolation(f"Invalid event {event_name} from state {trip.state.value}")
        trip.events.append((event_name, kwargs))
        if event_name == "AT_PICKUP":
            trip.state = TripState.AT_PICKUP
        elif event_name == "LOADED":
            trip.state = TripState.LOADED
        elif event_name == "IN_TRANSIT":
            trip.state = TripState.IN_TRANSIT
        elif event_name == "DELIVERED":
            trip.state = TripState.DELIVERED
            if kwargs.get("late_hours", 0) > 4: update_rating(carrier, "LATE_OVER_4H")
            else: update_rating(carrier, "ON_TIME")
        elif event_name == "CANCEL_SHIPPER":
            elapsed = self.current_minute - trip.matched_at
            if elapsed <= 60: fee = Decimal("0")
            elif elapsed <= 360: fee = Decimal("1000")
            else: fee = trip.base_price * Decimal("0.10")
            trip.cancellation_fee = fee
            trip.state = TripState.CANCELLED
            load.open = True
        elif event_name in {"CANCEL_CARRIER", "NO_SHOW"}:
            if event_name == "NO_SHOW" and self.current_minute < load.pickup_end:
                raise RuleViolation("Carrier no-show can only be recorded at or after pickup-window end")
            trip.cancellation_fee = Decimal("2000")
            update_rating(carrier, "CANCELLED")
            trip.state = TripState.CANCELLED
            load.open = True
        elif event_name == "ABORT":
            trip.state = TripState.ABORTED
            trip.settlement = {"detention": self._abort_detention(trip, truck), "abort_base_compensation": trip.base_price * Decimal("0.50")}
        elif event_name == "SETTLE":
            trip.state = TripState.SETTLED
            toll = Decimal(str(kwargs.get("toll_actual", trip.toll_actual)))
            trip.toll_actual = toll
            trip.pickup_detention_hours = Decimal(str(kwargs.get("pickup_detention_hours", 0)))
            trip.delivery_detention_hours = Decimal(str(kwargs.get("delivery_detention_hours", 0)))
            trip.settlement = settle_trip(trip, load, truck, carrier, shipper, carrier.annual_payout)
        self.logs.append(f"EVENT {trip_id}: {event_name} -> {trip.state.value}")
        return trip.state

    def _abort_detention(self, trip, truck):
        from src.settlement import detention_charge
        hours = max(Decimal(trip.pickup_detention_hours), Decimal("48"))
        return detention_charge(hours, truck.truck_type)[0]

    def execute_commands(self, commands):
        """Supported commands: ADVANCE, MATCH, COUNTER, EVENT. Registration data remains in Python."""
        for command in commands:
            op = command["op"].upper()
            if op == "ADVANCE": self.current_minute += int(command["minutes"])
            elif op == "MATCH": self.run_matching_cycle()
            elif op == "COUNTER": self.submit_counter(command["trip_id"], command["amount"], command.get("elapsed_minutes", 0))
            elif op == "EVENT": self.event(command["trip_id"], command["event"], **command.get("data", {}))
            else: raise ValueError(f"Unsupported command: {op}")

    def run_demo(self):
        self.run_matching_cycle()
        if not self.trips: return
        trip_id = sorted(self.trips)[0]
        self.event(trip_id, "AT_PICKUP")
        self.event(trip_id, "LOADED")
        self.event(trip_id, "IN_TRANSIT")
        self.event(trip_id, "DELIVERED", late_hours=0)
        self.event(trip_id, "SETTLE", toll_actual=500, pickup_detention_hours=7, delivery_detention_hours=6)

    def render_report(self):
        lines = ["FREIGHT EXCHANGE ENGINE REPORT", "=" * 36, "PRICE BREAKDOWNS"]
        for load in self.loads.values():
            if load.price_breakdown:
                p = load.price_breakdown
                lines.append(f"{load.load_id}: distance={p['distance_km']} km, chargeable={p['chargeable_km']} km, base=Rs {p['base_price']}, ratio={p['demand_supply_ratio']}, adjustments={p['total_adjustment_pct']}%, recommended=Rs {p['recommended_price']}")
        lines += ["", "MATCHING / EVENT LOG", *self.logs, "", "TRIP SETTLEMENTS"]
        for trip in self.trips.values():
            lines.append(f"{trip.trip_id}: state={trip.state.value}")
            if trip.settlement:
                for key, value in trip.settlement.items():
                    lines.append(f"  {key}: {value}")
        return "\n".join(lines)

"""Core FreightEngine orchestrating pricing, matching, bidding, lifecycle, and settlement."""

from decimal import Decimal

from config import (
    ABORT_THRESHOLD_HOURS,
    CARRIER_CANCEL_FEE,
    DEFAULT_EXTRA_STOP_FEE,
    DEFAULT_FUEL_INDEX_PCT,
    OFFER_EXPIRY_MINUTES,
)
from app.models.entities import Carrier, Load, Shipper, State, Trip, Truck
from app.services.bidding_service import counter_status
from app.services.exceptions import RuleError, rupee
from app.services.matching_service import eligible_trucks
from app.services.pricing_service import price_load, validate_load
from app.services.reporting_service import build_text_report
from app.services.settlement_service import settle
from app.services.trip_lifecycle_service import cancellation_fee, detention, update_rating


class FreightEngine:
    """Stateful freight exchange engine coordinating BR-01 through BR-30 workflows."""

    def __init__(
        self,
        distances: dict[tuple[str, str], int | float | Decimal],
        poor_cities: set[str] | list[str] | None = None,
        toll_caps: dict[tuple[str, str], int | float | Decimal] | None = None,
        fuel_index_pct: Decimal = DEFAULT_FUEL_INDEX_PCT,
        extra_stop_fee: Decimal = DEFAULT_EXTRA_STOP_FEE,
    ):
        self.distances = distances
        self.poor_cities = set(poor_cities or [])
        self.toll_caps = toll_caps or {}
        self.fuel_index_pct = Decimal(str(fuel_index_pct))
        self.extra_stop_fee = Decimal(str(extra_stop_fee))

        self.shippers: dict[str, Shipper] = {}
        self.carriers: dict[str, Carrier] = {}
        self.trucks: dict[str, Truck] = {}
        self.loads: dict[str, Load] = {}
        self.trips: dict[str, Trip] = {}

        self.logs: list[str] = []
        self.rejection_records: list[dict] = []
        self.offer_history: list[dict] = []
        self.now: int = 0
        self.offer_queue: dict[str, list[str]] = {}
        self.counter_pending: dict[str, dict] = {}

    def register_shipper(self, shipper: Shipper) -> None:
        self.shippers[shipper.id] = shipper

    def register_carrier(self, carrier: Carrier) -> None:
        self.carriers[carrier.id] = carrier

    def register_truck(self, truck: Truck) -> None:
        if truck.carrier_id not in self.carriers:
            raise RuleError("Register carrier before truck")
        self.trucks[truck.id] = truck

    def post_load(self, load: Load) -> dict:
        if load.shipper_id not in self.shippers:
            raise RuleError("Register shipper before load")
        validate_load(load)
        self.loads[load.id] = load
        return price_load(
            load,
            list(self.trucks.values()),
            list(self.loads.values()),
            self.distances,
            self.poor_cities,
            fuel_index_pct=self.fuel_index_pct,
            extra_stop_fee=self.extra_stop_fee,
        )

    def match_cycle(self) -> None:
        """Re-price open loads, filter/rank trucks, and issue top-ranked offers."""
        for load in sorted(self.loads.values(), key=lambda z: z.id):
            if not load.open:
                continue
            price_load(
                load,
                list(self.trucks.values()),
                list(self.loads.values()),
                self.distances,
                self.poor_cities,
                fuel_index_pct=self.fuel_index_pct,
                extra_stop_fee=self.extra_stop_fee,
            )
            ranked, rejected = eligible_trucks(
                load, list(self.trucks.values()), self.carriers, self.distances, self.now
            )
            self.logs.append(f"CYCLE {self.now} LOAD {load.id} PRICE Rs {load.recommended}")
            for tid, why in sorted(rejected.items()):
                self.logs.append(f" REJECT {tid}: {', '.join(why)}")
                self.rejection_records.append(
                    {"cycle_minute": self.now, "load_id": load.id, "truck_id": tid, "reasons": why}
                )
            if ranked:
                self.offer_queue[load.id] = [t.id for t in ranked[:3]]
                self._offer_next(load.id)
            else:
                self.logs.append(f" NO ELIGIBLE TRUCKS for {load.id}")

    def _offer_next(self, load_id: str) -> None:
        queue = self.offer_queue.get(load_id, [])
        if not queue:
            self.logs.append(f" EXHAUSTED OFFERS for {load_id}")
            return
        tid = queue.pop(0)
        load = self.loads[load_id]
        truck = self.trucks[tid]
        trip_id = f"TRIP-{load_id}"
        deadline = self.now + OFFER_EXPIRY_MINUTES
        trip = Trip(
            id=trip_id,
            load_id=load_id,
            truck_id=tid,
            carrier_id=truck.carrier_id,
            shipper_id=load.shipper_id,
            state=State.MATCHED,
            matched_at=self.now,
            agreed_price=load.recommended,
            base_price=load.price["base_price"],
            offer_deadline=deadline,
        )
        self.trips[trip_id] = trip
        self.offer_history.append(
            {"minute": self.now, "load_id": load_id, "truck_id": tid, "deadline": deadline, "status": "OFFERED"}
        )
        self.logs.append(f" OFFER {load_id} -> {tid}; response deadline {deadline}")

    def respond_offer(self, load_id: str, accept: bool, minute: int | None = None) -> str:
        trip = self.trips[f"TRIP-{load_id}"]
        at = self.now if minute is None else minute
        if at > trip.offer_deadline:
            self.logs.append(f" OFFER EXPIRED {load_id}")
            self._offer_next(load_id)
            return "EXPIRED"
        if accept:
            trip.accepted_at = at
            trip.state = State.MATCHED
            self.loads[load_id].open = False
            self.offer_history.append(
                {"minute": at, "load_id": load_id, "truck_id": trip.truck_id, "deadline": trip.offer_deadline, "status": "ACCEPTED"}
            )
            self.logs.append(f" ACCEPTED {load_id} by {trip.truck_id}")
            return "ACCEPTED"
        self.offer_history.append(
            {"minute": at, "load_id": load_id, "truck_id": trip.truck_id, "deadline": trip.offer_deadline, "status": "DECLINED"}
        )
        self.logs.append(f" DECLINED {load_id} by {trip.truck_id}")
        self._offer_next(load_id)
        return "DECLINED"

    def advance(self, minutes: int) -> None:
        self.now += int(minutes)
        for tid, trip in list(self.trips.items()):
            if trip.state == State.MATCHED and trip.accepted_at is None and self.now > trip.offer_deadline:
                self.logs.append(f" OFFER TIMEOUT {tid}")
                self._offer_next(trip.load_id)
            pending = self.counter_pending.get(tid)
            if pending and self.now > pending["deadline"]:
                self.logs.append(f" COUNTER LAPSED {tid}")
                del self.counter_pending[tid]

    def counter(self, trip_id: str, amount: Decimal | int | float) -> str:
        trip = self.trips[trip_id]
        status = counter_status(trip.agreed_price, amount, 0)
        if status == "SHIPPER_DECISION_REQUIRED":
            self.counter_pending[trip_id] = {"amount": Decimal(str(amount)), "deadline": self.now + 60}
        elif status == "AUTO_ACCEPTED":
            trip.agreed_price = Decimal(str(amount))
        self.logs.append(f" COUNTER {trip_id} Rs {amount}: {status}")
        return status

    def shipper_counter_decision(self, trip_id: str, accept: bool) -> str:
        pending = self.counter_pending.get(trip_id)
        if not pending:
            raise RuleError("No pending shipper counter decision")
        if self.now > pending["deadline"]:
            del self.counter_pending[trip_id]
            return "LAPSED"
        if accept:
            self.trips[trip_id].agreed_price = pending["amount"]
        del self.counter_pending[trip_id]
        return "ACCEPTED" if accept else "REJECTED"

    def event(self, trip_id: str, event: str, **data) -> State:
        trip = self.trips[trip_id]
        load = self.loads[trip.load_id]
        truck = self.trucks[trip.truck_id]
        carrier = self.carriers[trip.carrier_id]

        transitions = {
            "AT_PICKUP": (State.MATCHED, State.AT_PICKUP),
            "LOADED": (State.AT_PICKUP, State.LOADED),
            "IN_TRANSIT": (State.LOADED, State.IN_TRANSIT),
            "DELIVERED": (State.IN_TRANSIT, State.DELIVERED),
        }
        if event in transitions:
            old, new = transitions[event]
            if trip.state != old:
                raise RuleError(f"{event} invalid from {trip.state.value}")
            trip.state = new
            if event == "DELIVERED":
                update_rating(carrier, "LATE_OVER_4H" if data.get("late_hours", 0) > 4 else "ON_TIME")
        elif event == "CANCEL_SHIPPER":
            if trip.state != State.MATCHED:
                raise RuleError("Shipper cancellation only before AT_PICKUP")
            trip.cancel_fee = cancellation_fee(self.now - trip.matched_at, trip.base_price)
            trip.cancel_reason = "SHIPPER_CANCELLED"
            trip.state = State.CANCELLED
            load.open = True
        elif event == "CANCEL_CARRIER":
            if trip.accepted_at is None:
                raise RuleError("Carrier cancellation requires accepted offer")
            trip.cancel_fee = CARRIER_CANCEL_FEE
            trip.cancel_reason = "CARRIER_CANCELLED"
            update_rating(carrier, "CANCELLED")
            trip.state = State.CANCELLED
            load.open = True
        elif event == "NO_SHOW":
            if trip.state != State.MATCHED or self.now < load.pickup_end:
                raise RuleError("No-show only at/after pickup window end")
            trip.cancel_fee = CARRIER_CANCEL_FEE
            trip.cancel_reason = "CARRIER_NO_SHOW"
            update_rating(carrier, "CANCELLED")
            trip.state = State.CANCELLED
            load.open = True
        elif event == "ABORT":
            if trip.state != State.AT_PICKUP:
                raise RuleError("Abort only while at pickup")
            wait_hours = Decimal(str(data.get("pickup_detention_hours", 54)))
            if wait_hours <= ABORT_THRESHOLD_HOURS:
                raise RuleError("Carrier abort requires detention exceeding 48 hours")
            trip.pickup_detention = wait_hours
            charge, _ = detention(wait_hours, truck.truck_type)
            trip.settlement = {
                "detention": charge,
                "abort_base_compensation": rupee(trip.base_price * Decimal("0.5")),
            }
            trip.state = State.ABORTED
        elif event == "SETTLE":
            if trip.state != State.DELIVERED:
                raise RuleError("Settlement only after delivery")
            trip.pickup_detention = Decimal(str(data.get("pickup_detention_hours", 0)))
            trip.delivery_detention = Decimal(str(data.get("delivery_detention_hours", 0)))
            trip.toll_actual = Decimal(str(data.get("toll_actual", 0)))
            trip.settlement = settle(
                trip,
                load,
                truck,
                carrier,
                self.shippers[trip.shipper_id],
                self.toll_caps.get((load.origin, load.destination)),
            )
            trip.state = State.SETTLED
        else:
            raise RuleError(f"Unknown event {event}")

        self.logs.append(f" EVENT {trip_id}: {event} -> {trip.state.value}")
        return trip.state

    def run_demo(self) -> None:
        self.match_cycle()
        for load_id in list(self.offer_queue):
            trip = self.trips.get(f"TRIP-{load_id}")
            if trip and trip.accepted_at is None:
                self.respond_offer(load_id, True)
        for trip_id, trip in list(self.trips.items()):
            if trip.accepted_at is None:
                continue
            self.event(trip_id, "AT_PICKUP")
            self.event(trip_id, "LOADED")
            self.event(trip_id, "IN_TRANSIT")
            self.event(trip_id, "DELIVERED", late_hours=0)
            self.event(
                trip_id,
                "SETTLE",
                toll_actual=500,
                pickup_detention_hours=7,
                delivery_detention_hours=6,
            )

    def report(self) -> str:
        return build_text_report(self)

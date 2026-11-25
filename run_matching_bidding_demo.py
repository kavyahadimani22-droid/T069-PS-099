"""Focused demonstration of truck eligibility, ranking, 30-min timeout, and counter-bidding."""

from decimal import Decimal

from app.models.entities import Carrier, Load, Shipper, Truck
from app.services.exceptions import rupee
from app.services.freight_engine import FreightEngine


def main() -> None:
    engine = FreightEngine({("Bengaluru", "Chennai"): 350, ("Mysuru", "Bengaluru"): 145})
    engine.register_shipper(Shipper("SHP-1", "Acme Manufacturing", True))
    engine.register_carrier(Carrier("CAR-1", "Alpha Logistics", Decimal("4.7"), second_driver=True))
    engine.register_carrier(Carrier("CAR-2", "Beta Logistics", Decimal("4.3"), second_driver=True))
    engine.register_carrier(Carrier("CAR-3", "Blocked Low Rating", Decimal("2.7"), second_driver=True))

    engine.register_truck(Truck("TRK-A", "CAR-1", "17FT", Decimal(8), Decimal(17), "Bengaluru"))
    engine.register_truck(Truck("TRK-B", "CAR-2", "22FT", Decimal(14), Decimal(22), "Mysuru"))
    engine.register_truck(Truck("TRK-LOW", "CAR-3", "17FT", Decimal(8), Decimal(17), "Bengaluru"))

    engine.post_load(Load("LD-100", "SHP-1", "Bengaluru", "Chennai", Decimal(6), "17FT", 0, 480))
    engine.match_cycle()
    print(f"Initial offer: {engine.trips['TRIP-LD-100'].truck_id}")

    # Simulate 31-minute timeout -> falls back to next ranked truck (TRK-B)
    engine.advance(31)
    print(f"After 31m timeout: {engine.trips['TRIP-LD-100'].truck_id}")

    engine.respond_offer("LD-100", True)
    rec = engine.trips["TRIP-LD-100"].agreed_price
    counter = rupee(rec * Decimal("1.08"))
    status = engine.counter("TRIP-LD-100", counter)
    print(f"Counter Rs {counter} (+8% over Rs {rec}) -> {status}")
    decision = engine.shipper_counter_decision("TRIP-LD-100", True)
    print(f"Shipper decision -> {decision}; final agreed price Rs {engine.trips['TRIP-LD-100'].agreed_price}")


if __name__ == "__main__":
    main()

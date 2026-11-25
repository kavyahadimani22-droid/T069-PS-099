"""Focused demonstration of shipper cancel, carrier cancel, no-show, and >48h abort."""

from decimal import Decimal

from app.models.entities import Carrier, Load, Shipper, Truck
from app.services.freight_engine import FreightEngine


def main() -> None:
    engine = FreightEngine({("A", "B"): 200})
    engine.register_shipper(Shipper("S", "Shipper Co", True))
    engine.register_carrier(Carrier("C1", "Carrier One", Decimal("4.5"), second_driver=True))
    engine.register_carrier(Carrier("C2", "Carrier Two", Decimal("4.5"), second_driver=True))
    engine.register_carrier(Carrier("C3", "Carrier Three", Decimal("4.5"), second_driver=True))

    engine.register_truck(Truck("T1", "C1", "17FT", Decimal(8), Decimal(17), "A"))
    engine.register_truck(Truck("T2", "C2", "17FT", Decimal(8), Decimal(17), "A"))
    engine.register_truck(Truck("T3", "C3", "17FT", Decimal(8), Decimal(17), "A"))

    engine.post_load(Load("L1", "S", "A", "B", Decimal(5), "17FT", 0, 120))
    engine.post_load(Load("L2", "S", "A", "B", Decimal(5), "17FT", 0, 120))
    engine.post_load(Load("L3", "S", "A", "B", Decimal(5), "17FT", 0, 120))

    engine.match_cycle()
    for lid in ("L1", "L2", "L3"):
        engine.respond_offer(lid, True)

    engine.advance(125)
    engine.event("TRIP-L1", "CANCEL_SHIPPER")
    engine.event("TRIP-L2", "CANCEL_CARRIER")
    engine.event("TRIP-L3", "AT_PICKUP")
    engine.event("TRIP-L3", "ABORT", pickup_detention_hours=54)

    for tid in ("TRIP-L1", "TRIP-L2", "TRIP-L3"):
        t = engine.trips[tid]
        print(f"{tid}: state={t.state.value}, cancel_fee=Rs {t.cancel_fee}, settlement={t.settlement}")


if __name__ == "__main__":
    main()

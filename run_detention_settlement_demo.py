"""Focused demonstration of detention, toll caps, 6% platform fee, 5% GST/RCM, and TDS."""

from decimal import Decimal

from app.models.entities import Carrier, Load, Shipper, Truck
from app.services.freight_engine import FreightEngine


def main() -> None:
    engine = FreightEngine(
        {("Bengaluru", "Chennai"): 350},
        toll_caps={("Bengaluru", "Chennai"): 700},
    )
    engine.register_shipper(Shipper("SHP-1", "Acme Manufacturing", gst_registered=True))
    engine.register_carrier(Carrier("CAR-1", "SouthLine Logistics", Decimal("4.5"), annual_payout=Decimal("95000"), second_driver=True))
    engine.register_truck(Truck("TRK-1", "CAR-1", "17FT", Decimal(8), Decimal(17), "Bengaluru"))
    engine.post_load(Load("LD-200", "SHP-1", "Bengaluru", "Chennai", Decimal(6), "17FT", 0, 480))

    engine.match_cycle()
    engine.respond_offer("LD-200", True)
    for ev in ("AT_PICKUP", "LOADED", "IN_TRANSIT"):
        engine.event("TRIP-LD-200", ev)
    engine.event("TRIP-LD-200", "DELIVERED", late_hours=0)
    engine.event("TRIP-LD-200", "SETTLE", toll_actual=900, pickup_detention_hours=7, delivery_detention_hours=6)

    print("SETTLEMENT & TAX DEMO (BR-17..BR-25)")
    print("=" * 55)
    for k, v in engine.trips["TRIP-LD-200"].settlement.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()

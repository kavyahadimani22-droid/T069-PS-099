"""Focused demonstration of dynamic pricing rules (BR-01..BR-08, BR-29/30)."""

from decimal import Decimal

from app.models.entities import Load, Shipper, Truck
from app.services.freight_engine import FreightEngine


def main() -> None:
    distances = {
        ("Bengaluru", "Mysuru"): 145,
        ("Bengaluru", "Chennai"): 350,
        ("Bengaluru", "Delhi"): 2150,
    }
    engine = FreightEngine(distances, poor_cities={"Delhi"}, fuel_index_pct=Decimal("2"))
    engine.register_shipper(Shipper("SHP-1", "Demo Shipper", True))

    # Post 5 Bengaluru->Chennai LCV loads against 1 local LCV truck to trigger >4 surge (+30%)
    from app.models.entities import Carrier

    engine.register_carrier(Carrier("CAR-1", "Demo Carrier", Decimal("4.5")))
    engine.register_truck(Truck("TRK-1", "CAR-1", "LCV", Decimal(3), Decimal(10), "Bengaluru"))

    loads = [
        Load("LD-MIN", "SHP-1", "Bengaluru", "Mysuru", Decimal(2), "17FT", 0, 240, "GENERAL"),
        Load("LD-HAZ", "SHP-1", "Bengaluru", "Delhi", Decimal(20), "32FT_MXL", 0, 480, "HAZARDOUS"),
        Load("LD-PER", "SHP-1", "Bengaluru", "Chennai", Decimal(2), "LCV", 0, 300, "PERISHABLE", extra_stops=1),
    ]
    for i in range(4):
        loads.append(Load(f"LD-SURGE-{i}", "SHP-1", "Bengaluru", "Chennai", Decimal(2), "LCV", 0, 300))

    print("T069-PS-099 DYNAMIC PRICING DEMO")
    print("=" * 55)
    for load in loads:
        p = engine.post_load(load)
        print(
            f"{load.id} ({load.origin} -> {load.destination}, {load.truck_type}, {load.material}): "
            f"km={p['distance_km']} (billable={p['chargeable_km']}), base=Rs {p['base_price']}, "
            f"surge={p['surge_pct']}%, poor={p['backhaul_poor_pct']}%, mat={p['material_pct']}%, "
            f"fuel={p['fuel_index_pct']}%, stops=Rs {p['multi_drop_fee']} -> Recommended Rs {p['recommended_price']}"
        )


if __name__ == "__main__":
    main()

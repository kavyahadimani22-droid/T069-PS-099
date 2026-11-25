"""Master-data loaders for quick demos and CSV-based sample data packs."""

import csv
from decimal import Decimal
from pathlib import Path

from app.models.entities import Carrier, Load, Shipper, Truck
from app.services.freight_engine import FreightEngine


def _bool(val: str) -> bool:
    return str(val).strip().lower() in {"1", "true", "yes", "y"}


def create_engine() -> FreightEngine:
    """Build a compact illustrative FreightEngine instance (matches baseline quickstart)."""
    distances = {
        ("Bengaluru", "Chennai"): 350,
        ("Bengaluru", "Hyderabad"): 570,
        ("Bengaluru", "Mumbai"): 980,
        ("Bengaluru", "Pune"): 840,
        ("Bengaluru", "Mysuru"): 145,
        ("Bengaluru", "Coimbatore"): 360,
        ("Chennai", "Hyderabad"): 625,
        ("Chennai", "Coimbatore"): 500,
        ("Hyderabad", "Mumbai"): 710,
        ("Mumbai", "Pune"): 150,
        ("Delhi", "Mumbai"): 1420,
        ("Delhi", "Hyderabad"): 1550,
        ("Mysuru", "Coimbatore"): 200,
        ("Pune", "Hyderabad"): 560,
    }
    engine = FreightEngine(
        distances,
        poor_cities={"Delhi", "Coimbatore"},
        toll_caps={("Bengaluru", "Chennai"): 700, ("Chennai", "Bengaluru"): 700},
    )
    engine.register_shipper(Shipper("SHP-001", "Acme Manufacturing", True))
    engine.register_shipper(Shipper("SHP-002", "Fresh Foods Ltd", False))

    engine.register_carrier(Carrier("CAR-001", "SouthLine Logistics", Decimal("4.6"), second_driver=True))
    engine.register_carrier(Carrier("CAR-002", "Rapid Freight", Decimal("4.2")))
    engine.register_carrier(Carrier("CAR-003", "Budget Carriers", Decimal("3.7")))
    engine.register_carrier(Carrier("CAR-004", "Low Rated Transport", Decimal("2.8")))

    engine.register_truck(Truck("TRK-001", "CAR-001", "17FT", Decimal(8), Decimal(17), "Bengaluru", 0, Decimal(5), True))
    engine.register_truck(Truck("TRK-002", "CAR-002", "22FT", Decimal(14), Decimal(22), "Mysuru", 0, Decimal(8)))
    engine.register_truck(Truck("TRK-003", "CAR-003", "17FT", Decimal(7), Decimal(17), "Chennai", 0, Decimal(3)))
    engine.register_truck(Truck("TRK-004", "CAR-004", "17FT", Decimal(10), Decimal(17), "Bengaluru", 0, Decimal(2)))
    engine.register_truck(Truck("TRK-005", "CAR-001", "32FT_MXL", Decimal(25), Decimal(32), "Hyderabad", 0, Decimal(4), True))
    engine.register_truck(Truck("TRK-006", "CAR-002", "LCV", Decimal(3), Decimal(10), "Bengaluru", 0, Decimal(4)))

    engine.post_load(
        Load("LD-001", "SHP-001", "Bengaluru", "Chennai", Decimal(6), "17FT", 60, 480, "GENERAL", Decimal(14))
    )
    return engine


def load_engine_from_csv_dir(data_dir: str | Path, post_loads: bool = True) -> FreightEngine:
    """Hydrate a FreightEngine from the structured CSV files in sample_data/."""
    base = Path(data_dir)
    distances: dict[tuple[str, str], int] = {}
    with (base / "lanes.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            distances[(row["origin"], row["destination"])] = int(row["distance_km"])

    toll_caps: dict[tuple[str, str], Decimal] = {}
    with (base / "toll_caps.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            toll_caps[(row["origin"], row["destination"])] = Decimal(row["cap_amount"])

    poor_cities: set[str] = set()
    with (base / "backhaul_poor_cities.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            poor_cities.add(row["city"].strip())

    engine = FreightEngine(distances, poor_cities=poor_cities, toll_caps=toll_caps)

    with (base / "shippers.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            engine.register_shipper(Shipper(row["id"], row["name"], _bool(row["gst_registered"])))

    with (base / "carriers.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            engine.register_carrier(
                Carrier(
                    row["id"],
                    row["name"],
                    rating=Decimal(row["rating"]),
                    annual_payout=Decimal(row["annual_payout"]),
                    second_driver=_bool(row["second_driver"]),
                    active=_bool(row["active"]),
                )
            )

    with (base / "trucks.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            engine.register_truck(
                Truck(
                    row["id"],
                    row["carrier_id"],
                    row["truck_type"],
                    Decimal(row["capacity_tonnes"]),
                    Decimal(row["length_ft"]),
                    row["city"],
                    available_from=int(row["available_from"]),
                    hours_used=Decimal(row["hours_used"]),
                    haz_certified=_bool(row["haz_certified"]),
                    active=_bool(row["active"]),
                )
            )

    if post_loads and (base / "loads.csv").exists():
        with (base / "loads.csv").open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                engine.post_load(
                    Load(
                        row["id"],
                        row["shipper_id"],
                        row["origin"],
                        row["destination"],
                        Decimal(row["weight_tonnes"]),
                        row["truck_type"],
                        int(row["pickup_start"]),
                        int(row["pickup_end"]),
                        material=row["material"],
                        length_ft=Decimal(row["length_ft"]),
                        extra_stops=int(row.get("extra_stops", 0) or 0),
                    )
                )
    return engine

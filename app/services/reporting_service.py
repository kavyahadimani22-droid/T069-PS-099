"""Structured text reporting and CSV export utilities for T069-PS-099."""

import csv
from pathlib import Path

from app.services.exceptions import rupee


def build_text_report(engine) -> str:
    """Render a human-readable execution report covering pricing, logs, and settlements."""
    lines = [
        "T069-PS-099 FREIGHT EXCHANGE ENGINE REPORT",
        "=" * 60,
        f"Clock (minutes): {engine.now}",
        f"Shippers: {len(engine.shippers)} | Carriers: {len(engine.carriers)} | "
        f"Trucks: {len(engine.trucks)} | Loads: {len(engine.loads)} | Trips: {len(engine.trips)}",
        "",
        "1. DYNAMIC PRICE BREAKDOWNS",
        "-" * 60,
    ]
    for load in sorted(engine.loads.values(), key=lambda x: x.id):
        if not load.price:
            continue
        p = load.price
        lines.append(
            f"{load.id} ({load.origin} -> {load.destination}, {load.truck_type}, {load.material}): "
            f"km={p['distance_km']} (billable={p['chargeable_km']}), base=Rs {p['base_price']}, "
            f"ratio={p['demand_supply_ratio']:.2f}, surge={p['surge_pct']}%, "
            f"backhaul={p['return_load_pct']}%, poor={p['backhaul_poor_pct']}%, "
            f"material={p['material_pct']}%, recommended=Rs {p['recommended_price']}"
        )

    lines.extend(["", "2. MATCHING & EVENT LOG", "-" * 60, *engine.logs, "", "3. TRIP SETTLEMENTS", "-" * 60])
    for trip in sorted(engine.trips.values(), key=lambda x: x.id):
        lines.append(
            f"{trip.id}: state={trip.state.value} | load={trip.load_id} | "
            f"truck={trip.truck_id} | carrier={trip.carrier_id} | agreed=Rs {rupee(trip.agreed_price)}"
        )
        if trip.cancel_fee:
            lines.append(f"  cancellation_fee: Rs {rupee(trip.cancel_fee)}")
        if trip.cancel_reason:
            lines.append(f"  cancel_reason: {trip.cancel_reason}")
        for key, value in trip.settlement.items():
            lines.append(f"  {key}: {value}")

    lines.extend(["", "4. CARRIER RATINGS & CUMULATIVE PAYOUTS", "-" * 60])
    for carrier in sorted(engine.carriers.values(), key=lambda x: x.id):
        lines.append(
            f"{carrier.id} ({carrier.name}): rating={carrier.rating}, "
            f"annual_payout=Rs {rupee(carrier.annual_payout)}, second_driver={carrier.second_driver}"
        )
    return "\n".join(lines)


def _write_csv(path: Path, headers: list[str], rows: list[list]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(headers)
        writer.writerows(rows)
    return path


def export_csv_reports(engine, output_dir: str | Path) -> dict[str, Path]:
    """Export all structured CSV outputs to output_dir and return generated file paths."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    generated: dict[str, Path] = {}

    # 1. price_breakdowns.csv
    price_headers = [
        "load_id", "shipper_id", "origin", "destination", "truck_type", "material",
        "distance_km", "chargeable_km", "rate_per_km", "base_price",
        "open_loads", "available_trucks_200km", "demand_supply_ratio",
        "surge_pct", "return_load_count", "return_load_pct", "backhaul_poor_pct",
        "material_pct", "fuel_index_pct", "extra_stops", "multi_drop_fee",
        "total_adjustment_pct", "recommended_price", "open",
    ]
    price_rows = []
    for load in sorted(engine.loads.values(), key=lambda x: x.id):
        if not load.price:
            continue
        p = load.price
        price_rows.append([
            load.id, load.shipper_id, load.origin, load.destination, load.truck_type, load.material,
            p["distance_km"], p["chargeable_km"], p["rate_per_km"], p["base_price"],
            p["open_loads"], p["available_trucks_200km"], f"{p['demand_supply_ratio']:.2f}",
            p["surge_pct"], p["return_load_count"], p["return_load_pct"], p["backhaul_poor_pct"],
            p["material_pct"], p["fuel_index_pct"], p["extra_stops"], p["multi_drop_fee"],
            p["total_adjustment_pct"], p["recommended_price"], load.open,
        ])
    generated["price_breakdowns"] = _write_csv(out / "price_breakdowns.csv", price_headers, price_rows)

    # 2. trips.csv
    trip_headers = [
        "trip_id", "load_id", "truck_id", "carrier_id", "shipper_id", "state",
        "matched_at", "offer_deadline", "accepted_at", "base_price", "agreed_price",
        "cancel_fee", "cancel_reason",
    ]
    trip_rows = [
        [
            t.id, t.load_id, t.truck_id, t.carrier_id, t.shipper_id, t.state.value,
            t.matched_at, t.offer_deadline, "" if t.accepted_at is None else t.accepted_at,
            rupee(t.base_price), rupee(t.agreed_price), rupee(t.cancel_fee), t.cancel_reason,
        ]
        for t in sorted(engine.trips.values(), key=lambda x: x.id)
    ]
    generated["trips"] = _write_csv(out / "trips.csv", trip_headers, trip_rows)

    # 3. settlements.csv & 4. shipper_invoices.csv
    settlement_headers = [
        "trip_id", "load_id", "carrier_id", "state", "base_price", "freight",
        "pickup_detention", "delivery_detention", "detention_total", "toll",
        "carrier_gross", "platform_fee", "tds", "carrier_payout",
    ]
    invoice_headers = [
        "trip_id", "load_id", "shipper_id", "freight", "detention_total",
        "toll", "gst", "shipper_invoice", "rcm_flag",
    ]
    settlement_rows = []
    invoice_rows = []
    for t in sorted(engine.trips.values(), key=lambda x: x.id):
        s = t.settlement
        if not s:
            continue
        if "carrier_payout" in s:
            settlement_rows.append([
                t.id, t.load_id, t.carrier_id, t.state.value,
                s["base_price"], s["freight"], s["pickup_detention"], s["delivery_detention"],
                s["detention_total"], s["toll"], s["carrier_gross"], s["platform_fee"],
                s["tds"], s["carrier_payout"],
            ])
            invoice_rows.append([
                t.id, t.load_id, t.shipper_id, s["freight"], s["detention_total"],
                s["toll"], s["gst"], s["shipper_invoice"], s["rcm_flag"],
            ])
        elif "abort_base_compensation" in s:
            settlement_rows.append([
                t.id, t.load_id, t.carrier_id, t.state.value,
                rupee(t.base_price), s["abort_base_compensation"], s["detention"], 0,
                s["detention"], 0, s["detention"] + s["abort_base_compensation"], 0, 0,
                s["detention"] + s["abort_base_compensation"],
            ])
    generated["settlements"] = _write_csv(out / "settlements.csv", settlement_headers, settlement_rows)
    generated["shipper_invoices"] = _write_csv(out / "shipper_invoices.csv", invoice_headers, invoice_rows)

    # 5. carrier_ratings.csv
    rating_headers = ["carrier_id", "name", "rating", "annual_payout", "second_driver", "active"]
    rating_rows = [
        [c.id, c.name, c.rating, rupee(c.annual_payout), c.second_driver, c.active]
        for c in sorted(engine.carriers.values(), key=lambda x: x.id)
    ]
    generated["carrier_ratings"] = _write_csv(out / "carrier_ratings.csv", rating_headers, rating_rows)

    # 6. rejections.csv
    rejection_headers = ["cycle_minute", "load_id", "truck_id", "reasons"]
    rejection_rows = [
        [r["cycle_minute"], r["load_id"], r["truck_id"], "; ".join(r["reasons"])]
        for r in engine.rejection_records
    ]
    generated["rejections"] = _write_csv(out / "rejections.csv", rejection_headers, rejection_rows)

    return generated

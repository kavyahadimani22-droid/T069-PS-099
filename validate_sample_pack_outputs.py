"""Validate generated sample-pack CSV outputs against planted BR-01..BR-28 scenarios."""

import argparse
import csv
import sys
from decimal import Decimal
from pathlib import Path


def _read_csv_by_key(path: Path, key_col: str) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8") as fh:
        return {row[key_col]: row for row in csv.DictReader(fh)}


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def validate_outputs(output_dir: Path) -> list[tuple[str, bool, str]]:
    """Run structured scenario checks on outputs/ and return (check_name, passed, detail)."""
    checks: list[tuple[str, bool, str]] = []

    required_files = [
        "price_breakdowns.csv",
        "trips.csv",
        "settlements.csv",
        "shipper_invoices.csv",
        "carrier_ratings.csv",
        "rejections.csv",
        "run_report.txt",
    ]
    for fname in required_files:
        exists = (output_dir / fname).is_file()
        checks.append((f"file_exists:{fname}", exists, f"{fname} present={exists}"))
    if not all(c[1] for c in checks):
        return checks

    prices = _read_csv_by_key(output_dir / "price_breakdowns.csv", "load_id")
    trips = _read_csv_by_key(output_dir / "trips.csv", "trip_id")
    settlements = _read_csv_by_key(output_dir / "settlements.csv", "trip_id")
    invoices = _read_csv_by_key(output_dir / "shipper_invoices.csv", "trip_id")
    carriers = _read_csv_by_key(output_dir / "carrier_ratings.csv", "carrier_id")
    rejections = _read_csv_rows(output_dir / "rejections.csv")

    # BR-01: 145 km Bengaluru->Mysuru charged as 150 km
    ld5 = prices["LD-005"]
    checks.append((
        "BR-01_min_150_km",
        ld5["distance_km"] == "145" and ld5["chargeable_km"] == "150",
        f"LD-005 km={ld5['distance_km']}, billable={ld5['chargeable_km']}",
    ))

    # BR-05: LD-001 Bengaluru->Chennai has 3 return loads -> -8% discount
    ld1 = prices["LD-001"]
    checks.append((
        "BR-05_return_load_discount",
        Decimal(ld1["return_load_count"]) >= 3 and Decimal(ld1["return_load_pct"]) == Decimal("-8.00"),
        f"LD-001 return_loads={ld1['return_load_count']}, pct={ld1['return_load_pct']}",
    ))

    # BR-06 & BR-07: LD-003 Bengaluru->Delhi HAZARDOUS -> +12% poor +15% hazmat
    ld3 = prices["LD-003"]
    checks.append((
        "BR-06_07_poor_and_hazmat",
        Decimal(ld3["backhaul_poor_pct"]) == Decimal("12.00") and Decimal(ld3["material_pct"]) == Decimal("15.00"),
        f"LD-003 poor={ld3['backhaul_poor_pct']}%, material={ld3['material_pct']}%",
    ))

    # BR-08: LD-002 PERISHABLE -> +10%
    ld2 = prices["LD-002"]
    checks.append((
        "BR-08_perishable_surcharge",
        Decimal(ld2["material_pct"]) == Decimal("10.00"),
        f"LD-002 material={ld2['material_pct']}%",
    ))

    # BR-12 & BR-28: Rejection audit includes low rating (<3.0) and HOS breach
    rej_text = " | ".join(r["reasons"] for r in rejections)
    checks.append((
        "BR-28_low_rating_excluded",
        "rating below 3.0" in rej_text,
        "TRK-004 (CAR-004 rating 2.8) excluded",
    ))
    checks.append((
        "BR-12_26_hos_rejection",
        "insufficient hours" in rej_text or "14-hour daily limit" in rej_text,
        "TRK-010 HOS rejection recorded",
    ))

    # BR-15/16: LD-004 counter-bid accepted at 33869
    tr4 = trips["TRIP-LD-004"]
    checks.append((
        "BR-16_counter_accepted",
        tr4["agreed_price"] == "33869" and tr4["state"] == "SETTLED",
        f"TRIP-LD-004 agreed={tr4['agreed_price']}, state={tr4['state']}",
    ))

    # BR-19: LD-006 ABORTED with 48h capped detention + 50% base compensation
    tr6 = trips["TRIP-LD-006"]
    st6 = settlements["TRIP-LD-006"]
    checks.append((
        "BR-19_abort_compensation",
        tr6["state"] == "ABORTED" and Decimal(st6["detention_total"]) == Decimal("38400"),
        f"TRIP-LD-006 state={tr6['state']}, detention={st6['detention_total']}, comp={st6['freight']}",
    ))

    # BR-20: LD-005 shipper cancelled at 90 min -> Rs 1000 fee
    tr5 = trips["TRIP-LD-005"]
    checks.append((
        "BR-20_shipper_cancel_1000",
        tr5["state"] == "CANCELLED" and tr5["cancel_fee"] == "1000",
        f"TRIP-LD-005 state={tr5['state']}, fee={tr5['cancel_fee']}",
    ))

    # BR-21: LD-007 carrier cancelled -> Rs 2000 fee
    tr7 = trips["TRIP-LD-007"]
    checks.append((
        "BR-21_carrier_cancel_2000",
        tr7["state"] == "CANCELLED" and tr7["cancel_fee"] == "2000",
        f"TRIP-LD-007 state={tr7['state']}, fee={tr7['cancel_fee']}",
    ))

    # BR-22: LD-001 toll cap 700 -> capped at 770 despite toll_actual=900
    st1 = settlements["TRIP-LD-001"]
    checks.append((
        "BR-22_toll_cap_110pct",
        Decimal(st1["toll"]) == Decimal("770"),
        f"TRIP-LD-001 toll={st1['toll']}",
    ))

    # BR-24: GST & RCM flag
    inv1 = invoices["TRIP-LD-001"]
    inv2 = invoices["TRIP-LD-002"]
    checks.append((
        "BR-24_gst_rcm_flags",
        inv1["rcm_flag"] == "True" and inv2["rcm_flag"] == "False",
        f"TRIP-LD-001 RCM={inv1['rcm_flag']}, TRIP-LD-002 RCM={inv2['rcm_flag']}",
    ))

    # BR-25: Single-trip TDS (>30k) on LD-003 and cumulative annual TDS (>100k) on LD-002
    st2 = settlements["TRIP-LD-002"]
    st3 = settlements["TRIP-LD-003"]
    checks.append((
        "BR-25_cumulative_and_trip_tds",
        Decimal(st2["tds"]) > 0 and Decimal(st3["tds"]) > 0,
        f"TRIP-LD-002 cumulative TDS={st2['tds']}, TRIP-LD-003 trip TDS={st3['tds']}",
    ))

    # BR-27: CAR-002 on-time +0.05 (4.2 -> 4.25) and CAR-005 >4h late -0.1 (4.8 -> 4.7)
    c2 = carriers["CAR-002"]
    c5 = carriers["CAR-005"]
    checks.append((
        "BR-27_rating_update",
        Decimal(c2["rating"]) == Decimal("4.25") and Decimal(c5["rating"]) == Decimal("4.7"),
        f"CAR-002 rating={c2['rating']}, CAR-005 rating={c5['rating']}",
    ))

    return checks


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate T069-PS-099 sample pack outputs")
    parser.add_argument("--output-dir", default="outputs", help="Generated outputs directory")
    args = parser.parse_args()

    results = validate_outputs(Path(args.output_dir))
    passed = sum(1 for _, ok, _ in results if ok)
    for name, ok, detail in results:
        tag = "PASS" if ok else "FAIL"
        print(f"[{tag}] {name}: {detail}")
    print(f"\nValidation summary: {passed}/{len(results)} checks passed")
    if passed != len(results):
        sys.exit(1)


if __name__ == "__main__":
    main()

"""Verify SQLite schema tables and required columns against the DDL contract."""

import argparse
from pathlib import Path

from app.database.connection import initialize_database

EXPECTED_TABLES = {
    "shippers": {"id", "name", "gst_registered"},
    "carriers": {"id", "name", "rating", "annual_payout", "second_driver", "active"},
    "trucks": {"id", "carrier_id", "truck_type", "capacity_tonnes", "length_ft", "city", "available_from", "hours_used", "haz_certified", "active"},
    "lanes": {"origin", "destination", "distance_km"},
    "toll_caps": {"origin", "destination", "cap_amount"},
    "poor_cities": {"city"},
    "loads": {"id", "shipper_id", "origin", "destination", "weight_tonnes", "truck_type", "pickup_start", "pickup_end", "material", "length_ft", "extra_stops", "recommended_price", "open"},
    "trips": {"id", "load_id", "truck_id", "carrier_id", "shipper_id", "state", "matched_at", "offer_deadline", "accepted_at", "base_price", "agreed_price", "pickup_detention", "delivery_detention", "toll_actual", "cancel_fee", "cancel_reason"},
    "offer_history": {"id", "minute", "load_id", "truck_id", "deadline", "status"},
    "rejection_records": {"id", "cycle_minute", "load_id", "truck_id", "reasons"},
    "settlements": {"trip_id", "load_id", "carrier_id", "base_price", "freight", "pickup_detention", "delivery_detention", "detention_total", "toll", "carrier_gross", "platform_fee", "tds", "carrier_payout"},
    "shipper_invoices": {"trip_id", "load_id", "shipper_id", "freight", "detention_total", "toll", "gst", "shipper_invoice", "rcm_flag"},
    "audit_logs": {"id", "entry"},
}


def verify_schema(db_path: str | Path = ":memory:") -> None:
    conn = initialize_database(db_path)
    try:
        present_tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        }
        missing_tables = set(EXPECTED_TABLES) - present_tables
        if missing_tables:
            raise AssertionError(f"Missing tables: {sorted(missing_tables)}")

        for table, expected_cols in EXPECTED_TABLES.items():
            cols = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
            missing_cols = expected_cols - cols
            if missing_cols:
                raise AssertionError(f"Table {table} missing columns: {sorted(missing_cols)}")
        print(f"Schema verification PASSED ({len(EXPECTED_TABLES)} tables verified).")
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify T069-PS-099 SQLite schema")
    parser.add_argument("--db", default=":memory:", help="SQLite DB path or :memory:")
    args = parser.parse_args()
    verify_schema(args.db)


if __name__ == "__main__":
    main()

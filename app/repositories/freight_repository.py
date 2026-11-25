"""SQLite persistence repository for FreightEngine entities, settlements, and audit logs."""

import sqlite3

from app.services.exceptions import rupee


class FreightRepository:
    """Persists and queries FreightEngine snapshots in SQLite."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def save_engine_snapshot(self, engine) -> None:
        """Persist master data, loads, trips, settlements, invoices, and logs atomically."""
        with self.conn:
            for table in (
                "audit_logs",
                "shipper_invoices",
                "settlements",
                "rejection_records",
                "offer_history",
                "trips",
                "loads",
                "trucks",
                "carriers",
                "shippers",
                "poor_cities",
                "toll_caps",
                "lanes",
            ):
                self.conn.execute(f"DELETE FROM {table}")

            self.conn.executemany(
                "INSERT INTO lanes (origin, destination, distance_km) VALUES (?, ?, ?)",
                [(a, b, int(km)) for (a, b), km in engine.distances.items()],
            )
            self.conn.executemany(
                "INSERT INTO toll_caps (origin, destination, cap_amount) VALUES (?, ?, ?)",
                [(a, b, str(cap)) for (a, b), cap in engine.toll_caps.items()],
            )
            self.conn.executemany(
                "INSERT INTO poor_cities (city) VALUES (?)",
                [(c,) for c in sorted(engine.poor_cities)],
            )
            self.conn.executemany(
                "INSERT INTO shippers (id, name, gst_registered) VALUES (?, ?, ?)",
                [(s.id, s.name, int(s.gst_registered)) for s in engine.shippers.values()],
            )
            self.conn.executemany(
                "INSERT INTO carriers (id, name, rating, annual_payout, second_driver, active) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (c.id, c.name, str(c.rating), str(c.annual_payout), int(c.second_driver), int(c.active))
                    for c in engine.carriers.values()
                ],
            )
            self.conn.executemany(
                "INSERT INTO trucks (id, carrier_id, truck_type, capacity_tonnes, length_ft, city, "
                "available_from, hours_used, haz_certified, active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        t.id,
                        t.carrier_id,
                        t.truck_type,
                        str(t.capacity_tonnes),
                        str(t.length_ft),
                        t.city,
                        int(t.available_from),
                        str(t.hours_used),
                        int(t.haz_certified),
                        int(t.active),
                    )
                    for t in engine.trucks.values()
                ],
            )
            self.conn.executemany(
                "INSERT INTO loads (id, shipper_id, origin, destination, weight_tonnes, truck_type, "
                "pickup_start, pickup_end, material, length_ft, extra_stops, recommended_price, open) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        l.id,
                        l.shipper_id,
                        l.origin,
                        l.destination,
                        str(l.weight_tonnes),
                        l.truck_type,
                        int(l.pickup_start),
                        int(l.pickup_end),
                        l.material,
                        str(l.length_ft),
                        int(l.extra_stops),
                        str(l.recommended),
                        int(l.open),
                    )
                    for l in engine.loads.values()
                ],
            )
            self.conn.executemany(
                "INSERT INTO trips (id, load_id, truck_id, carrier_id, shipper_id, state, matched_at, "
                "offer_deadline, accepted_at, base_price, agreed_price, pickup_detention, delivery_detention, "
                "toll_actual, cancel_fee, cancel_reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        t.id,
                        t.load_id,
                        t.truck_id,
                        t.carrier_id,
                        t.shipper_id,
                        t.state.value,
                        int(t.matched_at),
                        int(t.offer_deadline),
                        t.accepted_at,
                        str(rupee(t.base_price)),
                        str(rupee(t.agreed_price)),
                        str(t.pickup_detention),
                        str(t.delivery_detention),
                        str(t.toll_actual),
                        str(rupee(t.cancel_fee)),
                        t.cancel_reason,
                    )
                    for t in engine.trips.values()
                ],
            )
            self.conn.executemany(
                "INSERT INTO offer_history (minute, load_id, truck_id, deadline, status) VALUES (?, ?, ?, ?, ?)",
                [(o["minute"], o["load_id"], o["truck_id"], o["deadline"], o["status"]) for o in engine.offer_history],
            )
            self.conn.executemany(
                "INSERT INTO rejection_records (cycle_minute, load_id, truck_id, reasons) VALUES (?, ?, ?, ?)",
                [
                    (r["cycle_minute"], r["load_id"], r["truck_id"], "; ".join(r["reasons"]))
                    for r in engine.rejection_records
                ],
            )

            for t in engine.trips.values():
                s = t.settlement
                if s and "carrier_payout" in s:
                    self.conn.execute(
                        "INSERT INTO settlements (trip_id, load_id, carrier_id, base_price, freight, "
                        "pickup_detention, delivery_detention, detention_total, toll, carrier_gross, "
                        "platform_fee, tds, carrier_payout) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            t.id,
                            t.load_id,
                            t.carrier_id,
                            str(s["base_price"]),
                            str(s["freight"]),
                            str(s["pickup_detention"]),
                            str(s["delivery_detention"]),
                            str(s["detention_total"]),
                            str(s["toll"]),
                            str(s["carrier_gross"]),
                            str(s["platform_fee"]),
                            str(s["tds"]),
                            str(s["carrier_payout"]),
                        ),
                    )
                    self.conn.execute(
                        "INSERT INTO shipper_invoices (trip_id, load_id, shipper_id, freight, "
                        "detention_total, toll, gst, shipper_invoice, rcm_flag) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            t.id,
                            t.load_id,
                            t.shipper_id,
                            str(s["freight"]),
                            str(s["detention_total"]),
                            str(s["toll"]),
                            str(s["gst"]),
                            str(s["shipper_invoice"]),
                            int(bool(s["rcm_flag"])),
                        ),
                    )

            self.conn.executemany(
                "INSERT INTO audit_logs (entry) VALUES (?)",
                [(line,) for line in engine.logs],
            )

    def fetch_summary_counts(self) -> dict[str, int]:
        """Return row counts across all persisted tables for verification and status checks."""
        tables = [
            "shippers",
            "carriers",
            "trucks",
            "lanes",
            "loads",
            "trips",
            "settlements",
            "shipper_invoices",
            "offer_history",
            "rejection_records",
            "audit_logs",
        ]
        return {
            tbl: self.conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            for tbl in tables
        }

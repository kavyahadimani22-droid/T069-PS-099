-- T069-PS-099 Financial Settlement, Shipper Invoice, and Audit Log Schema

CREATE TABLE IF NOT EXISTS settlements (
    trip_id TEXT PRIMARY KEY REFERENCES trips(id),
    load_id TEXT NOT NULL REFERENCES loads(id),
    carrier_id TEXT NOT NULL REFERENCES carriers(id),
    base_price TEXT NOT NULL,
    freight TEXT NOT NULL,
    pickup_detention TEXT NOT NULL,
    delivery_detention TEXT NOT NULL,
    detention_total TEXT NOT NULL,
    toll TEXT NOT NULL,
    carrier_gross TEXT NOT NULL,
    platform_fee TEXT NOT NULL,
    tds TEXT NOT NULL,
    carrier_payout TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS shipper_invoices (
    trip_id TEXT PRIMARY KEY REFERENCES trips(id),
    load_id TEXT NOT NULL REFERENCES loads(id),
    shipper_id TEXT NOT NULL REFERENCES shippers(id),
    freight TEXT NOT NULL,
    detention_total TEXT NOT NULL,
    toll TEXT NOT NULL,
    gst TEXT NOT NULL,
    shipper_invoice TEXT NOT NULL,
    rcm_flag INTEGER NOT NULL CHECK (rcm_flag IN (0, 1))
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry TEXT NOT NULL
);

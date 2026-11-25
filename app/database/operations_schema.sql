-- T069-PS-099 Operational Load, Trip, Offer, and Rejection Schema

CREATE TABLE IF NOT EXISTS loads (
    id TEXT PRIMARY KEY,
    shipper_id TEXT NOT NULL REFERENCES shippers(id),
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    weight_tonnes TEXT NOT NULL,
    truck_type TEXT NOT NULL,
    pickup_start INTEGER NOT NULL,
    pickup_end INTEGER NOT NULL,
    material TEXT NOT NULL DEFAULT 'GENERAL',
    length_ft TEXT NOT NULL DEFAULT '0',
    extra_stops INTEGER NOT NULL DEFAULT 0,
    recommended_price TEXT NOT NULL DEFAULT '0',
    open INTEGER NOT NULL DEFAULT 1 CHECK (open IN (0, 1))
);

CREATE TABLE IF NOT EXISTS trips (
    id TEXT PRIMARY KEY,
    load_id TEXT NOT NULL REFERENCES loads(id),
    truck_id TEXT NOT NULL REFERENCES trucks(id),
    carrier_id TEXT NOT NULL REFERENCES carriers(id),
    shipper_id TEXT NOT NULL REFERENCES shippers(id),
    state TEXT NOT NULL,
    matched_at INTEGER NOT NULL,
    offer_deadline INTEGER NOT NULL,
    accepted_at INTEGER,
    base_price TEXT NOT NULL,
    agreed_price TEXT NOT NULL,
    pickup_detention TEXT NOT NULL DEFAULT '0',
    delivery_detention TEXT NOT NULL DEFAULT '0',
    toll_actual TEXT NOT NULL DEFAULT '0',
    cancel_fee TEXT NOT NULL DEFAULT '0',
    cancel_reason TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS offer_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    minute INTEGER NOT NULL,
    load_id TEXT NOT NULL REFERENCES loads(id),
    truck_id TEXT NOT NULL REFERENCES trucks(id),
    deadline INTEGER NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rejection_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_minute INTEGER NOT NULL,
    load_id TEXT NOT NULL REFERENCES loads(id),
    truck_id TEXT NOT NULL REFERENCES trucks(id),
    reasons TEXT NOT NULL
);

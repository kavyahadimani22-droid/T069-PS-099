-- T069-PS-099 Master Data Schema (SQLite / ANSI-compatible DDL)

CREATE TABLE IF NOT EXISTS shippers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    gst_registered INTEGER NOT NULL DEFAULT 0 CHECK (gst_registered IN (0, 1))
);

CREATE TABLE IF NOT EXISTS carriers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    rating TEXT NOT NULL DEFAULT '4.0',
    annual_payout TEXT NOT NULL DEFAULT '0',
    second_driver INTEGER NOT NULL DEFAULT 0 CHECK (second_driver IN (0, 1)),
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1))
);

CREATE TABLE IF NOT EXISTS trucks (
    id TEXT PRIMARY KEY,
    carrier_id TEXT NOT NULL REFERENCES carriers(id),
    truck_type TEXT NOT NULL,
    capacity_tonnes TEXT NOT NULL,
    length_ft TEXT NOT NULL,
    city TEXT NOT NULL,
    available_from INTEGER NOT NULL DEFAULT 0,
    hours_used TEXT NOT NULL DEFAULT '0',
    haz_certified INTEGER NOT NULL DEFAULT 0 CHECK (haz_certified IN (0, 1)),
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1))
);

CREATE TABLE IF NOT EXISTS lanes (
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    distance_km INTEGER NOT NULL CHECK (distance_km > 0),
    PRIMARY KEY (origin, destination)
);

CREATE TABLE IF NOT EXISTS toll_caps (
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    cap_amount TEXT NOT NULL,
    PRIMARY KEY (origin, destination)
);

CREATE TABLE IF NOT EXISTS poor_cities (
    city TEXT PRIMARY KEY
);

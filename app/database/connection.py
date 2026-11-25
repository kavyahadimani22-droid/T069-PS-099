"""SQLite database connection and schema bootstrap utilities."""

import sqlite3
from pathlib import Path

SCHEMA_FILES = [
    "schema.sql",
    "operations_schema.sql",
    "settlement_schema.sql",
]


def get_connection(db_path: str | Path) -> sqlite3.Connection:
    """Open a SQLite connection with foreign-key enforcement enabled."""
    path = Path(db_path)
    if str(path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def initialize_database(db_path: str | Path) -> sqlite3.Connection:
    """Create database tables from ordered SQL schema files and return the connection."""
    conn = get_connection(db_path)
    schema_dir = Path(__file__).resolve().parent
    for filename in SCHEMA_FILES:
        sql = (schema_dir / filename).read_text(encoding="utf-8")
        conn.executescript(sql)
    conn.commit()
    return conn

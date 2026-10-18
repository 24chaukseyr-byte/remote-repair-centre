"""SQLite helpers and schema for the Remote Mobile Repair Centre."""
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name     TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    phone         TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS repair_requests (
    request_id     TEXT PRIMARY KEY,
    user_id        INTEGER NOT NULL,
    brand          TEXT NOT NULL,
    model          TEXT NOT NULL,
    imei           TEXT NOT NULL,
    issue_type     TEXT NOT NULL,
    description    TEXT NOT NULL,
    pickup_date    TEXT NOT NULL,
    pickup_address TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'Submitted',
    created_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
"""


def connect(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path):
    conn = connect(path)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def next_request_id(conn):
    """Return the next request ID: REQ-0001, REQ-0002, ..."""
    row = conn.execute(
        "SELECT MAX(CAST(SUBSTR(request_id, 5) AS INTEGER)) AS m FROM repair_requests"
    ).fetchone()
    return f"REQ-{(row['m'] or 0) + 1:04d}"

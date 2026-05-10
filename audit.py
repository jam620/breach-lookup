import sqlite3
from datetime import datetime, timezone


CREATE_AUDIT_TABLE = """
CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT    NOT NULL,
    username    TEXT    NOT NULL,
    field       TEXT    NOT NULL,
    results_cnt INTEGER NOT NULL,
    ip_address  TEXT
);
"""


def init_audit_table(conn: sqlite3.Connection) -> None:
    conn.execute(CREATE_AUDIT_TABLE)
    conn.commit()


def log_query(
    conn: sqlite3.Connection,
    *,
    username: str,
    field: str,
    results_cnt: int,
    ip_address: str | None,
) -> None:
    # q (search value) is intentionally never stored here — PII protection
    conn.execute(
        """INSERT INTO audit_log (timestamp, username, field, results_cnt, ip_address)
           VALUES (?, ?, ?, ?, ?)""",
        (
            datetime.now(timezone.utc).isoformat(),
            username,
            field,
            results_cnt,
            ip_address or "unknown",
        ),
    )
    conn.commit()

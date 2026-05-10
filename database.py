import csv
import sqlite3
from pathlib import Path

from config import settings
from audit import init_audit_table

DB_PATH = Path(settings.DB_PATH)
CSV_PATH = Path(__file__).parent / settings.CSV_PATH

# Column mapping: CSV header → normalized DB column name
CSV_COLUMN_MAP = {
    "id": "id",
    "nombres": "nombres",
    "apellidos": "apellidos",
    "documento": "documento",
    "fecha_nacimiento": "fecha_nacimiento",
    "email": "email",
    "movil": "movil",
    "telefono": "telefono",
    "pais origen": "pais_origen",
    "fecha de registro": "fecha_registro",
    "usuario": "usuario",
    "friend terpel": "friend_terpel",
}

CREATE_BREACH_TABLE = """
CREATE TABLE IF NOT EXISTS breach_records (
    id               INTEGER,
    nombres          TEXT,
    apellidos        TEXT,
    documento        TEXT,
    fecha_nacimiento TEXT,
    email            TEXT,
    movil            TEXT,
    telefono         TEXT,
    pais_origen      TEXT,
    fecha_registro   TEXT,
    usuario          TEXT,
    friend_terpel    TEXT
);
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_documento  ON breach_records(documento);",
    "CREATE INDEX IF NOT EXISTS idx_email      ON breach_records(email);",
    "CREATE INDEX IF NOT EXISTS idx_movil      ON breach_records(movil);",
    "CREATE INDEX IF NOT EXISTS idx_telefono   ON breach_records(telefono);",
    "CREATE INDEX IF NOT EXISTS idx_usuario    ON breach_records(usuario);",
    "CREATE INDEX IF NOT EXISTS idx_nombres    ON breach_records(nombres);",
    "CREATE INDEX IF NOT EXISTS idx_apellidos  ON breach_records(apellidos);",
]


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _import_csv(conn: sqlite3.Connection) -> int:
    with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = []
        for raw in reader:
            # Normalise header names
            row = {CSV_COLUMN_MAP.get(k, k): v.strip() if v else None for k, v in raw.items()}
            # Skip completely empty rows
            if not any(row.values()):
                continue
            # Convert numeric-looking id to int when possible
            try:
                row["id"] = int(float(row["id"])) if row.get("id") else None
            except (ValueError, TypeError):
                row["id"] = None
            rows.append((
                row.get("id"),
                row.get("nombres"),
                row.get("apellidos"),
                row.get("documento"),
                row.get("fecha_nacimiento"),
                row.get("email"),
                row.get("movil"),
                row.get("telefono"),
                row.get("pais_origen"),
                row.get("fecha_registro"),
                row.get("usuario"),
                row.get("friend_terpel"),
            ))

    conn.executemany(
        """INSERT INTO breach_records
           (id, nombres, apellidos, documento, fecha_nacimiento,
            email, movil, telefono, pais_origen, fecha_registro,
            usuario, friend_terpel)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        rows,
    )
    conn.commit()
    return len(rows)


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    conn.execute(CREATE_BREACH_TABLE)
    for idx_sql in CREATE_INDEXES:
        conn.execute(idx_sql)
    conn.commit()

    count = conn.execute("SELECT COUNT(*) FROM breach_records").fetchone()[0]
    if count == 0:
        imported = _import_csv(conn)
        print(f"[DB] Imported {imported} records from CSV.")
    else:
        print(f"[DB] breach_records already has {count} rows — skipping import.")

    init_audit_table(conn)
    conn.close()

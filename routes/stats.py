from fastapi import APIRouter

from database import get_connection
from models import StatsResponse

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("", response_model=StatsResponse)
def stats():
    conn = get_connection()
    try:
        total_records: int = conn.execute(
            "SELECT COUNT(*) FROM breach_records"
        ).fetchone()[0]

        top_paises = [
            dict(row)
            for row in conn.execute(
                """SELECT pais_origen AS value, COUNT(*) AS count
                   FROM breach_records
                   WHERE pais_origen IS NOT NULL AND pais_origen != ''
                   GROUP BY pais_origen
                   ORDER BY count DESC
                   LIMIT 10"""
            ).fetchall()
        ]

        top_dominios_email = [
            dict(row)
            for row in conn.execute(
                """SELECT LOWER(SUBSTR(email, INSTR(email, '@') + 1)) AS value,
                          COUNT(*) AS count
                   FROM breach_records
                   WHERE email LIKE '%@%'
                   GROUP BY value
                   ORDER BY count DESC
                   LIMIT 10"""
            ).fetchall()
        ]

        nulls_row = conn.execute(
            """SELECT
                 SUM(CASE WHEN nombres       = '' OR nombres       IS NULL THEN 1 ELSE 0 END) AS nombres,
                 SUM(CASE WHEN apellidos     = '' OR apellidos     IS NULL THEN 1 ELSE 0 END) AS apellidos,
                 SUM(CASE WHEN documento     = '' OR documento     IS NULL THEN 1 ELSE 0 END) AS documento,
                 SUM(CASE WHEN email         = '' OR email         IS NULL THEN 1 ELSE 0 END) AS email,
                 SUM(CASE WHEN movil         = '' OR movil         IS NULL THEN 1 ELSE 0 END) AS movil,
                 SUM(CASE WHEN telefono      = '' OR telefono      IS NULL THEN 1 ELSE 0 END) AS telefono,
                 SUM(CASE WHEN pais_origen   = '' OR pais_origen   IS NULL THEN 1 ELSE 0 END) AS pais_origen,
                 SUM(CASE WHEN usuario       = '' OR usuario       IS NULL THEN 1 ELSE 0 END) AS usuario,
                 SUM(CASE WHEN friend_terpel = '' OR friend_terpel IS NULL THEN 1 ELSE 0 END) AS friend_terpel
               FROM breach_records"""
        ).fetchone()

        nulos_por_campo: dict[str, int] = dict(nulls_row)
    finally:
        conn.close()

    return StatsResponse(
        total_records=total_records,
        top_paises=top_paises,
        top_dominios_email=top_dominios_email,
        nulos_por_campo=nulos_por_campo,
    )

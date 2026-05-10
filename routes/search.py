from fastapi import APIRouter, HTTPException, Query, Request, status

from audit import log_query
from database import get_connection
from models import BreachRecord, SearchResponse

router = APIRouter(prefix="/api/search", tags=["search"])

# Columns searched when field == "__all__"
_ALL_COLS = [
    "nombres", "apellidos", "documento", "fecha_nacimiento",
    "email", "movil", "telefono", "pais_origen",
    "fecha_registro", "usuario", "friend_terpel",
]

# Whitelist maps validated field name → actual column name (defence in depth)
_FIELD_TO_COL: dict[str, str] = {col: col for col in _ALL_COLS} | {"documento": "documento"}

_VALID_FIELDS = {
    "__all__", "documento", "email", "movil", "telefono",
    "nombres", "apellidos", "usuario",
}


def _build_where(field: str, like_val: str) -> tuple[str, list]:
    if field == "__all__":
        clauses = " OR ".join(f"LOWER({col}) LIKE ?" for col in _ALL_COLS)
        params = [like_val] * len(_ALL_COLS)
    else:
        clauses = f"LOWER({field}) LIKE ?"
        params = [like_val]
    return clauses, params


@router.get("", response_model=SearchResponse)
def search(
    request: Request,
    q: str = Query(..., min_length=1, description="Término de búsqueda"),
    field: str = Query(default="__all__", description="Campo objetivo o __all__"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    q = q.strip()
    if not q:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="q cannot be empty")

    if field not in _VALID_FIELDS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"field must be one of {sorted(_VALID_FIELDS)}",
        )

    like_val = f"%{q.lower()}%"
    where_clause, params = _build_where(field, like_val)

    conn = get_connection()
    try:
        total = conn.execute(
            f"SELECT COUNT(*) FROM breach_records WHERE {where_clause}",
            params,
        ).fetchone()[0]

        rows = conn.execute(
            f"SELECT * FROM breach_records WHERE {where_clause} LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()

        results = [BreachRecord.from_row(row) for row in rows]

        ip = request.client.host if request.client else None
        log_query(conn, username="anonymous", field=field, results_cnt=total, ip_address=ip)
    finally:
        conn.close()

    return SearchResponse(
        total=total,
        results=results,
        query_field=field,
        page_offset=offset,
        page_limit=limit,
    )

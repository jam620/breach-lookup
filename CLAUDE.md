# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

Breach Lookup App — herramienta interna DFIR/OSINT (FastAPI + SQLite) que permite buscar registros en un dataset de 34,219 personas filtrado desde `Breach.csv`. El dataset proviene de una investigación Terpel (empresa de combustibles, Panamá). Sin autenticación (uso en red local controlada). Cada consulta se registra en audit_log.

## Running the server

```bash
cd /root/Terpel/breach-lookup
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

On first boot `init_db()` imports the CSV automatically if `breach_records` is empty. Subsequent boots skip import.

## Testing endpoints (curl)

```bash
# Login
curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Terpel2024!"}' | python3 -m json.tool

# Health (no auth required)
curl http://localhost:8000/health

# Search (replace TOKEN)
curl -s "http://localhost:8000/api/search?q=gmail&field=email&limit=10" \
  -H "Authorization: Bearer TOKEN"
```

## Architecture

```
config.py      — Pydantic Settings; reads .env; single source of truth for all config
database.py    — init_db(), get_connection(); CSV→SQLite import on first run
models.py      — All Pydantic schemas: BreachRecord, SearchRequest/Response,
                 LoginRequest, TokenResponse, StatsResponse
auth.py        — FastAPI router at /api/auth; login endpoint + get_current_user() dependency
main.py        — App factory: lifespan(init_db), CORS, router registration, /health
routes/
  search.py    — GET /api/search (Sprint 2, not yet implemented)
  stats.py     — GET /api/stats  (Sprint 2, not yet implemented)
audit.py       — audit_log table + log_query() (Sprint 2, not yet implemented)
static/        — Frontend HTML served via StaticFiles (Sprint 3)
data/
  breach.db    — SQLite database (gitignored)
```

## Data layer rules

- `get_connection()` sets `row_factory = sqlite3.Row` — always access columns by name, not index.
- **All SQL must use `?` placeholders.** Never interpolate user input into SQL strings.
- The CSV has space-separated headers (`pais origen`, `fecha de registro`, `friend terpel`); `database.py` normalises them to underscores via `CSV_COLUMN_MAP` before insert.
- `breach_records` is read-only from the API. No INSERT/UPDATE/DELETE routes against it.
- The search value `q` is **never** stored in `audit_log` — only field, result count, username, IP, timestamp.

## Security invariants

- Sin middleware de auth — deploy solo en red interna controlada.
- JWT secret comes from `settings.JWT_SECRET` (`.env`). Never hardcode it.
- In production (`ENVIRONMENT=production`), `/docs`, `/redoc`, and `/openapi.json` are disabled — `main.py` passes `docs_url=None` conditionally.
- Rate limiting via `slowapi` must be applied in Sprint 4 (20 req/min per IP).
- CORS `allow_origins=["*"]` is acceptable for development; must be restricted in production.

## Search logic (for routes/search.py)

```python
# field == "__all__"  → OR across all text columns
# field == specific   → single column
# Always: WHERE LOWER(col) LIKE ? with value = f"%{q.lower()}%"
```

Valid search fields: `__all__`, `documento`, `email`, `movil`, `telefono`, `nombres`, `apellidos`, `usuario`.

## Valid fields (SearchRequest)

Defined in `models.py → SearchField.ALLOWED`. Adding a new field requires updating `ALLOWED` and the SQL builder in `routes/search.py`.

## Configuration (.env)

| Variable | Default | Notes |
|---|---|---|
| `CSV_PATH` | `../Breach.csv` | Relative to `breach-lookup/` directory |
| `DB_PATH` | `./data/breach.db` | Created automatically |
| `JWT_SECRET` | *(must be set)* | Long random string in production |
| `JWT_EXPIRE_HOURS` | `8` | |
| `APP_USERNAME` | `admin` | Single admin user |
| `APP_PASSWORD` | `Terpel2024!` | Change in production |
| `ENVIRONMENT` | `development` | Set to `production` to disable /docs |

## Sprint status

| Sprint | Scope | Status |
|---|---|---|
| 1 | DB init, CSV import, models, auth | ✅ Complete |
| 2 | GET /api/search, audit_log, GET /api/stats, full main.py | ⬜ Pending |
| 3 | Frontend HTML (login modal, fetch-based search, stats sidebar) | ⬜ Pending |
| 4 | Rate limiting, security headers, Dockerfile, docker-compose | ⬜ Pending |

## Files that must stay out of git

`Breach.csv`, `Breach_Sheet1.csv`, `data/breach.db`, `.env` — these contain PII and credentials.

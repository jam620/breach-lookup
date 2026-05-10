from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from config import settings
from database import get_connection, init_db
from limiter import limiter
import auth
from routes import search, stats

_PROD = settings.ENVIRONMENT == "production"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Breach Lookup API",
    version="1.0.0",
    docs_url="/docs"         if not _PROD else None,
    redoc_url="/redoc"       if not _PROD else None,
    openapi_url="/openapi.json" if not _PROD else None,
    lifespan=lifespan,
)

# ── Rate limiting ──────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ── CORS ───────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Security headers ───────────────────────────────────────────────────────
@app.middleware("http")
async def security_headers(request: Request, call_next) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"]  = "nosniff"
    response.headers["X-Frame-Options"]         = "DENY"
    response.headers["X-XSS-Protection"]        = "1; mode=block"
    response.headers["Referrer-Policy"]         = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline';"
    )
    if _PROD:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
    return response

# ── Routers ────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(search.router)
app.include_router(stats.router)


@app.get("/health", tags=["meta"])
def health():
    conn = get_connection()
    try:
        records = conn.execute("SELECT COUNT(*) FROM breach_records").fetchone()[0]
    finally:
        conn.close()
    return {"status": "ok", "records": records, "environment": settings.ENVIRONMENT}


# Mount AFTER all API routes so /api/* and /health take priority
app.mount("/", StaticFiles(directory="static", html=True), name="static")

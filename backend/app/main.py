"""
Factory Management System — FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.core.config import settings
from app.middleware.audit_middleware import AuditRequestMiddleware
from app.routers import auth, users, sections, documents, warehouse, logs
from app.utils.responses import success_response
from app.utils.exceptions import register_exception_handlers

# ── Rate Limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks (e.g., warm connection pool, cache init)
    yield
    # Shutdown tasks (e.g., flush logs, close connections)


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Enterprise Factory Management System — MVP Backend",
    docs_url="/api/docs"     if settings.DEBUG else None,
    redoc_url="/api/redoc"   if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# ── Register custom exception handlers ────────────────────────────────────────
register_exception_handlers(app)

# ── Middleware (order matters — outermost first) ───────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(AuditRequestMiddleware)        # request logging

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.TRUSTED_HOSTS,
)

# ── Routers ───────────────────────────────────────────────────────────────────
V1 = "/api/v1"

app.include_router(auth.router,      prefix=f"{V1}/auth",      tags=["Authentication"])
app.include_router(users.router,     prefix=f"{V1}/users",     tags=["User Management"])
app.include_router(sections.router,  prefix=f"{V1}/sections",  tags=["Sections"])
app.include_router(documents.router, prefix=f"{V1}/documents", tags=["SOP Documents"])
app.include_router(warehouse.router, prefix=f"{V1}/warehouse", tags=["Warehouse"])
app.include_router(logs.router,      prefix=f"{V1}/logs",      tags=["Audit Logs"])


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check():
    return success_response(data={"status": "healthy", "version": "1.0.0"})

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.core.config import get_settings
from src.api.core.db import init_db_schema
from src.api.routers import (
    applications,
    auth,
    documents,
    health,
    inspections,
    payments,
    ticketing,
    workflow,
)

openapi_tags = [
    {"name": "health", "description": "Service health and diagnostics."},
    {"name": "auth", "description": "Authentication, JWT issuance, and MFA scaffolding."},
    {"name": "applications", "description": "Application lifecycle endpoints (submission, status, etc.)."},
    {"name": "workflow", "description": "Workflow/BPM and task management endpoints."},
    {"name": "inspections", "description": "Inspection creation and tracking."},
    {"name": "documents", "description": "Document metadata/content management boundaries (metadata persisted)."},
    {"name": "ticketing", "description": "Helpdesk/ticketing module boundaries."},
    {"name": "payments", "description": "Payment gateway boundaries (persistence implemented; gateway still stubbed)."},
]


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Entry point contract:
      - Initializes DB schema at startup using database migration SQL.
      - Registers modular routers under their prefixes.
      - Exposes OpenAPI docs via /docs and schema at /openapi.json.

    Environment variables:
      - JWT_SECRET_KEY (required in production)
      - DATABASE_URL (optional; if absent, reads database/db_connection.txt)
      - CORS_ALLOW_ORIGINS (optional, comma-separated; default 'http://localhost:3000')
    """
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description="Enterprise-grade Unified Digital Platform backend API (modular routers; JWT auth; Postgres persistence).",
        version=settings.app_version,
        openapi_tags=openapi_tags,
    )

    allow_origins = settings.cors_allow_origins

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def _startup() -> None:
        # Initialize required backend tables idempotently.
        init_db_schema()

    @app.get(
        "/docs/help",
        tags=["health"],
        summary="Docs usage help",
        description="Quick usage notes for authentication and common calls.",
        operation_id="docs_help",
    )
    def docs_help():
        """Docs usage help.

        Returns:
          - Helpful notes for interacting with the API.
        """
        return {
            "auth": {
                "register": "POST /auth/register {email,password} -> {access_token}",
                "login": "POST /auth/login {email,password[,mfa_code]} -> {access_token}",
                "me": "GET /auth/me with Authorization: Bearer <token>",
                "mfa_enroll_stub": "POST /auth/mfa/enroll with Authorization header",
            },
            "notes": [
                "Most endpoints require Authorization: Bearer <access_token>.",
                "MFA is scaffolding only in this step; real TOTP validation not implemented yet.",
            ],
        }

    # Routers
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(applications.router)
    app.include_router(workflow.router)
    app.include_router(inspections.router)
    app.include_router(documents.router)
    app.include_router(ticketing.router)
    app.include_router(payments.router)

    return app


app = create_app()

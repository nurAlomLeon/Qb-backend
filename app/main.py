from __future__ import annotations

from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy.engine import Engine

from app.api.v1 import api_router
from app.core.config import Settings, get_settings
from app.core.errors import register_error_handlers
from app.core.rate_limit import RateLimitMiddleware
from app.db.session import create_db_engine, create_session_factory


def create_app(
    settings: Optional[Settings] = None,
    engine: Optional[Engine] = None,
) -> FastAPI:
    settings = settings or get_settings()
    engine = engine or create_db_engine(settings.database_url)

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        debug=settings.debug,
    )
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)

    app.add_middleware(
        RateLimitMiddleware,
        per_minute=settings.rate_limit_per_minute,
        auth_per_minute=settings.auth_rate_limit_per_minute,
    )
    app.add_middleware(GZipMiddleware, minimum_size=500)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(app)
    app.include_router(api_router)

    @app.get("/healthz", tags=["health"])
    def healthz() -> dict:
        return {"status": "ok", "environment": settings.environment}

    from app.admin.setup import setup_admin

    setup_admin(app, engine, settings)

    return app


app = create_app()

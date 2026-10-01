from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    auth,
    bookmarks,
    config,
    live_exams,
    papers,
    progress,
    questions,
    search,
    sessions,
    units,
    version,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(config.router)
api_router.include_router(units.router)
api_router.include_router(papers.router)
api_router.include_router(questions.router)
api_router.include_router(live_exams.router)
api_router.include_router(search.router)
api_router.include_router(version.router)
api_router.include_router(auth.router)
api_router.include_router(bookmarks.router)
api_router.include_router(sessions.router)
api_router.include_router(progress.router)

from __future__ import annotations

import hmac
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_app_settings, get_db
from app.core.config import Settings
from app.models.content import Paper, Question, Subject, Unit
from app.models.university import University
from app.schemas.admin import (
    AdminImportPayload,
    AdminImportReport,
    AdminPaperCreate,
    AdminPaperOut,
    AdminPingOut,
    AdminSubjectCreate,
    AdminSubjectOut,
    AdminUnitCreate,
    AdminUnitOut,
    AdminUniversityCreate,
    AdminUniversityOut,
)
from app.schemas.common import Envelope
from app.services.importing import import_questions

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin_key(
    x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key"),
    settings: Settings = Depends(get_app_settings),
) -> None:
    if not settings.admin_api_key:
        raise HTTPException(status_code=503, detail="Admin API is disabled.")
    if not x_admin_key or not hmac.compare_digest(
        x_admin_key, settings.admin_api_key
    ):
        raise HTTPException(status_code=401, detail="Invalid admin key.")


@router.get("/ping", response_model=Envelope[AdminPingOut])
def ping(
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key),
) -> Envelope[AdminPingOut]:
    return Envelope(
        data=AdminPingOut(
            ok=True,
            universities=db.scalar(select(func.count(University.id))) or 0,
            subjects=db.scalar(select(func.count(Subject.id))) or 0,
            papers=db.scalar(select(func.count(Paper.id))) or 0,
            questions=db.scalar(select(func.count(Question.id))) or 0,
        )
    )


@router.get("/universities", response_model=Envelope[List[AdminUniversityOut]])
def list_universities(
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key),
) -> Envelope[List[AdminUniversityOut]]:
    rows = (
        db.execute(select(University).order_by(University.slug))
        .scalars()
        .all()
    )
    return Envelope(data=[AdminUniversityOut.model_validate(row) for row in rows])


@router.post("/universities", response_model=Envelope[AdminUniversityOut])
def create_university(
    payload: AdminUniversityCreate,
    response: Response,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key),
) -> Envelope[AdminUniversityOut]:
    existing = db.execute(
        select(University).where(University.slug == payload.slug)
    ).scalar_one_or_none()
    if existing is not None:
        response.status_code = 200
        return Envelope(data=AdminUniversityOut.model_validate(existing))

    university = University(
        slug=payload.slug,
        name_bn=payload.name_bn,
        name_en=payload.name_en,
        logo_url=payload.logo_url,
        theme=payload.theme,
    )
    db.add(university)
    db.commit()
    db.refresh(university)
    response.status_code = 201
    return Envelope(data=AdminUniversityOut.model_validate(university))


@router.get(
    "/universities/{university_id}/units",
    response_model=Envelope[List[AdminUnitOut]],
)
def list_units(
    university_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key),
) -> Envelope[List[AdminUnitOut]]:
    rows = (
        db.execute(
            select(Unit)
            .where(Unit.university_id == university_id)
            .order_by(Unit.sort_order, Unit.id)
        )
        .scalars()
        .all()
    )
    return Envelope(data=[AdminUnitOut.model_validate(row) for row in rows])


@router.post("/units", response_model=Envelope[AdminUnitOut])
def create_unit(
    payload: AdminUnitCreate,
    response: Response,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key),
) -> Envelope[AdminUnitOut]:
    university = db.get(University, payload.university_id)
    if university is None:
        raise HTTPException(status_code=404, detail="University not found.")

    existing = db.execute(
        select(Unit).where(
            Unit.university_id == payload.university_id,
            Unit.letter == payload.letter,
        )
    ).scalar_one_or_none()
    if existing is not None:
        response.status_code = 200
        return Envelope(data=AdminUnitOut.model_validate(existing))

    unit = Unit(
        university_id=payload.university_id,
        letter=payload.letter,
        title_bn=payload.title_bn,
        title_en=payload.title_en,
        faculty_bn=payload.faculty_bn,
        subjects_label=payload.subjects_label,
        sort_order=payload.sort_order,
    )
    db.add(unit)
    db.commit()
    db.refresh(unit)
    response.status_code = 201
    return Envelope(data=AdminUnitOut.model_validate(unit))


@router.get("/subjects", response_model=Envelope[List[AdminSubjectOut]])
def list_subjects(
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key),
) -> Envelope[List[AdminSubjectOut]]:
    rows = (
        db.execute(select(Subject).order_by(Subject.sort_order, Subject.id))
        .scalars()
        .all()
    )
    return Envelope(data=[AdminSubjectOut.model_validate(row) for row in rows])


@router.post("/subjects", response_model=Envelope[AdminSubjectOut])
def create_subject(
    payload: AdminSubjectCreate,
    response: Response,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key),
) -> Envelope[AdminSubjectOut]:
    existing = db.execute(
        select(Subject).where(Subject.code == payload.code)
    ).scalar_one_or_none()
    if existing is not None:
        response.status_code = 200
        return Envelope(data=AdminSubjectOut.model_validate(existing))

    subject = Subject(
        code=payload.code,
        label_bn=payload.label_bn,
        label_en=payload.label_en,
        icon=payload.icon,
        color=payload.color,
        sort_order=payload.sort_order,
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)
    response.status_code = 201
    return Envelope(data=AdminSubjectOut.model_validate(subject))


@router.get("/units/{unit_id}/papers", response_model=Envelope[List[AdminPaperOut]])
def list_papers(
    unit_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key),
) -> Envelope[List[AdminPaperOut]]:
    rows = (
        db.execute(
            select(Paper)
            .where(Paper.unit_id == unit_id)
            .order_by(Paper.year.desc())
        )
        .scalars()
        .all()
    )
    return Envelope(data=[AdminPaperOut.model_validate(row) for row in rows])


@router.post("/papers", response_model=Envelope[AdminPaperOut])
def create_paper(
    payload: AdminPaperCreate,
    response: Response,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key),
) -> Envelope[AdminPaperOut]:
    unit = db.get(Unit, payload.unit_id)
    if unit is None or unit.university_id != payload.university_id:
        raise HTTPException(status_code=404, detail="Unit not found.")

    existing = db.execute(
        select(Paper).where(
            Paper.unit_id == payload.unit_id,
            Paper.year == payload.year,
        )
    ).scalar_one_or_none()
    if existing is not None:
        response.status_code = 200
        return Envelope(data=AdminPaperOut.model_validate(existing))

    paper = Paper(
        university_id=payload.university_id,
        unit_id=payload.unit_id,
        year=payload.year,
        label_bn=payload.label_bn,
        status=payload.status,
        question_count=payload.question_count,
        duration_minutes=payload.duration_minutes,
        subjects_label=payload.subjects_label,
        is_published=payload.is_published,
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)
    response.status_code = 201
    return Envelope(data=AdminPaperOut.model_validate(paper))


@router.post(
    "/papers/{paper_id}/import",
    response_model=Envelope[AdminImportReport],
)
def import_paper_questions(
    paper_id: int,
    payload: AdminImportPayload,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key),
) -> Envelope[AdminImportReport]:
    paper = db.get(Paper, paper_id)
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found.")
    if payload.mode not in ("upsert", "skip"):
        raise HTTPException(status_code=422, detail="mode must be upsert or skip.")

    items = [
        question.model_dump(exclude_none=False)
        for question in payload.questions
    ]
    try:
        report = import_questions(db, paper, items, mode=payload.mode)
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Import failed: {cls}: {err}".format(
                cls=exc.__class__.__name__, err=str(exc)[:200]
            ),
        ) from exc
    return Envelope(
        data=AdminImportReport(
            created=report["created"],
            updated=report["updated"],
            skipped=report["skipped"],
            errors=report["errors"][:50],
            question_count=report["question_count"],
        )
    )

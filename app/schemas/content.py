from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class UniversityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    name_bn: str
    name_en: str
    logo_url: Optional[str] = None
    theme: Optional[dict] = None


class AppConfigOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    min_app_version: str
    latest_app_version: str
    force_update: bool
    sync_message: Optional[str] = None


class UnitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    letter: str
    title_bn: str
    title_en: Optional[str] = None
    faculty_bn: str
    subjects_label: str
    sort_order: int = 0
    paper_count: int = 0
    year_count: int = 0
    question_count: int = 0


class SubjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    label_bn: str
    label_en: str
    icon: Optional[str] = None
    color: Optional[str] = None
    sort_order: int = 0


class SubjectBreakdownOut(BaseModel):
    code: str
    label_bn: str
    question_count: int


class PaperOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    unit_id: int
    year: int
    label_bn: str
    status: str
    question_count: int
    duration_minutes: int
    subjects_label: str
    is_published: bool


class PaperDetailOut(PaperOut):
    subjects: List[SubjectBreakdownOut] = []


class OptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    letter: str
    text: str
    image_url: Optional[str] = None


class QuestionSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    paper_id: int
    serial: int
    subject_code: str
    subject_label_bn: str
    chapter_bn: str
    stem_bn: str
    stem_en: str
    difficulty: str
    analytics_percent: int
    options: List[OptionOut] = []
    images: List[str] = []


class QuestionDetailOut(QuestionSummaryOut):
    correct_index: int
    correct_letter: str
    explanation_bn: str
    explanation_en: Optional[str] = None
    shortcut_bn: Optional[str] = None
    mark: Optional[float] = None


class SearchResultOut(BaseModel):
    question_id: int
    paper_id: int
    serial: int
    subject_code: str
    stem_bn: str
    snippet: str


class VersionOut(BaseModel):
    latest: str
    min_supported: str
    force_update: bool
    message: Optional[str] = None


class LiveExamOut(BaseModel):
    id: int
    paper_id: int
    title_bn: str
    subtitle_bn: Optional[str] = None
    unit_title_bn: str
    starts_at: datetime
    ends_at: Optional[datetime] = None
    duration_minutes: int
    question_count: int
    participants: int
    status: str


class ConfigOut(BaseModel):
    university: UniversityOut
    config: AppConfigOut
    units: List[UnitOut]
    content_version: int

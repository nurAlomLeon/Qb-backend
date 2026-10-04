from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AdminUniversityCreate(BaseModel):
    slug: str = Field(min_length=2, max_length=32)
    name_bn: str = Field(min_length=1, max_length=120)
    name_en: str = Field(min_length=1, max_length=120)
    logo_url: Optional[str] = None
    theme: Optional[dict] = None


class AdminUniversityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name_bn: str
    name_en: str
    is_active: bool


class AdminUnitCreate(BaseModel):
    university_id: int
    letter: str = Field(min_length=1, max_length=8)
    title_bn: str = Field(min_length=1, max_length=80)
    title_en: Optional[str] = None
    faculty_bn: str = Field(min_length=1, max_length=120)
    subjects_label: str = Field(default="", max_length=160)
    sort_order: int = 0


class AdminUnitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    university_id: int
    letter: str
    title_bn: str
    faculty_bn: str
    subjects_label: str
    sort_order: int
    is_active: bool


class AdminSubjectCreate(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    label_bn: str = Field(min_length=1, max_length=80)
    label_en: str = Field(min_length=1, max_length=80)
    icon: Optional[str] = None
    color: Optional[str] = None
    sort_order: int = 0


class AdminSubjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    label_bn: str
    label_en: str
    sort_order: int


class AdminPaperCreate(BaseModel):
    university_id: int
    unit_id: int
    year: int
    label_bn: str = Field(min_length=1, max_length=80)
    status: str = "fresh"
    question_count: int = 0
    duration_minutes: int = 90
    subjects_label: str = ""
    is_published: bool = True


class AdminPaperOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    university_id: int
    unit_id: int
    year: int
    label_bn: str
    status: str
    question_count: int
    duration_minutes: int
    subjects_label: str
    is_published: bool


class AdminQuestionOptionIn(BaseModel):
    letter: Optional[str] = None
    text: str = ""
    text_html: Optional[str] = None
    image_url: Optional[str] = None


class AdminQuestionIn(BaseModel):
    serial: Optional[int] = None
    subject_code: str
    chapter_bn: str = ""
    stem_bn: str = ""
    stem_html: Optional[str] = None
    stem_en: Optional[str] = None
    options: List[AdminQuestionOptionIn]
    correct_index: Optional[int] = None
    correct_letter: Optional[str] = None
    explanation_bn: str = ""
    explanation_html: Optional[str] = None
    shortcut_bn: Optional[str] = None
    difficulty: str = "medium"
    mark: Optional[float] = None
    source: Optional[str] = None
    source_pk: Optional[str] = None
    images: List[str] = []
    explanation_images: List[str] = []
    tags: Optional[dict] = None
    raw_json: Optional[dict] = None


class AdminImportPayload(BaseModel):
    mode: str = "upsert"
    questions: List[AdminQuestionIn]


class AdminImportReport(BaseModel):
    created: int
    updated: int
    skipped: int
    errors: List[str] = []
    question_count: int


class AdminPingOut(BaseModel):
    ok: bool
    universities: int
    subjects: int
    papers: int
    questions: int

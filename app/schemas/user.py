from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DeviceRegisterIn(BaseModel):
    device_id: str = Field(min_length=8, max_length=64)
    display_name: Optional[str] = Field(default=None, max_length=80)
    target_university_slug: Optional[str] = Field(default=None, max_length=32)
    target_unit_id: Optional[int] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: str
    display_name: Optional[str] = None
    target_university_id: Optional[int] = None
    target_unit_id: Optional[int] = None
    score_percent: int
    weekly_solved: int


class DeviceRegisterOut(BaseModel):
    token: str
    user: UserOut


class BookmarkCreateIn(BaseModel):
    question_id: int


class BookmarkOut(BaseModel):
    id: int
    question_id: int
    paper_id: int
    unit_id: int
    serial: int
    subject_code: str
    subject_label_bn: str
    year_tag: str
    stem_bn: str
    correct_letter: str
    correct_text: str
    created_at: datetime


class SessionAnswerIn(BaseModel):
    question_id: int
    selected_index: Optional[int] = Field(default=None, ge=0, le=3)
    time_spent_ms: Optional[int] = Field(default=None, ge=0)


class SessionSubmitIn(BaseModel):
    paper_id: int
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    answers: List[SessionAnswerIn] = []


class SessionSubmitOut(BaseModel):
    session_id: int
    answered: int
    correct: int
    wrong: int
    skipped: int
    score: float
    accuracy: float
    score_percent: int
    weekly_solved: int


class ProgressRecentOut(BaseModel):
    session_id: int
    unit_id: int
    unit_title_bn: str
    year_label: str
    paper_id: int
    subject_code: Optional[str] = None
    subject_label_bn: Optional[str] = None
    chapter_bn: Optional[str] = None
    answered: int
    total: int
    percent: int


class ProgressStatsOut(BaseModel):
    score_percent: int
    weekly_solved: int
    total_sessions: int
    total_answered: int
    total_correct: int

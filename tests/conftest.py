from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security import generate_app_key, hash_app_key, hash_password
from app.db.base import Base
from app.db.fts import create_fts_schema
from app.db.session import create_db_engine, create_session_factory
from app.main import create_app
from app.models.admin import AdminUser
from app.models.content import Paper, Question, QuestionOption, Subject, Unit
from app.models.university import AppConfig, AppKey, ContentMeta, University

LETTERS = ["ক", "খ", "গ", "ঘ"]


def _make_question(
    university: University,
    paper: Paper,
    unit: Unit,
    subject: Subject,
    serial: int,
    stem_bn: str,
    stem_en: str,
    correct_index: int = 0,
    is_published: bool = True,
) -> Question:
    question = Question(
        university_id=university.id,
        paper_id=paper.id,
        unit_id=unit.id,
        subject_id=subject.id,
        serial=serial,
        chapter_bn="১ম পত্র • অধ্যায় ১",
        stem_bn=stem_bn,
        stem_en=stem_en,
        correct_index=correct_index,
        explanation_bn="ব্যাখ্যা: {stem}".format(stem=stem_bn),
        shortcut_bn="শর্টকাট টেকনিক",
        difficulty="easy",
        analytics_percent=60,
        analytics_attempts=100,
        analytics_correct=60,
        is_published=is_published,
    )
    for order in range(4):
        question.options.append(
            QuestionOption(
                letter=LETTERS[order],
                text="Option {n} for Q{serial}".format(n=order + 1, serial=serial),
                sort_order=order,
            )
        )
    return question


def _seed(session_factory) -> dict:
    with session_factory() as db:
        du = University(slug="du", name_bn="ঢাকা বিশ্ববিদ্যালয়", name_en="University of Dhaka")
        ru = University(slug="ru", name_bn="রাজশাহী বিশ্ববিদ্যালয়", name_en="University of Rajshahi")
        db.add_all([du, ru])
        db.flush()

        du_key = "test-du-key"
        ru_key = "test-ru-key"
        db.add_all(
            [
                AppKey(university_id=du.id, key_hash=hash_app_key(du_key), label="test"),
                AppKey(university_id=ru.id, key_hash=hash_app_key(ru_key), label="test"),
                AppConfig(
                    university_id=du.id,
                    min_app_version="2.0.0",
                    latest_app_version="2.4.0",
                    force_update=False,
                    sync_message="sync active",
                ),
                ContentMeta(university_id=du.id, content_version=7),
                ContentMeta(university_id=ru.id, content_version=1),
            ]
        )

        physics = Subject(code="physics", label_bn="পদার্থবিজ্ঞান", label_en="Physics", sort_order=0)
        chemistry = Subject(code="chemistry", label_bn="রসায়ন", label_en="Chemistry", sort_order=1)
        db.add_all([physics, chemistry])
        db.flush()

        k_unit = Unit(
            university_id=du.id,
            letter="ক",
            title_bn="ক ইউনিট",
            faculty_bn="বিজ্ঞান অনুষদ",
            subjects_label="পদার্থ • রসায়ন",
            sort_order=0,
        )
        ru_unit = Unit(
            university_id=ru.id,
            letter="ক",
            title_bn="ক ইউনিট",
            faculty_bn="বিজ্ঞান অনুষদ",
            subjects_label="পদার্থ",
            sort_order=0,
        )
        db.add_all([k_unit, ru_unit])
        db.flush()

        paper_2024 = Paper(
            university_id=du.id,
            unit_id=k_unit.id,
            year=2024,
            label_bn="২০২৩-২৪ শিক্ষাবর্ষ",
            status="fresh",
            question_count=4,
            duration_minutes=90,
            subjects_label="পদার্থ • রসায়ন",
        )
        paper_2023 = Paper(
            university_id=du.id,
            unit_id=k_unit.id,
            year=2023,
            label_bn="২০২২-২৩ শিক্ষাবর্ষ",
            status="attempted",
            question_count=2,
            duration_minutes=90,
            subjects_label="পদার্থ",
        )
        ru_paper = Paper(
            university_id=ru.id,
            unit_id=ru_unit.id,
            year=2024,
            label_bn="২০২৩-২৪ শিক্ষাবর্ষ",
            status="fresh",
            question_count=1,
            duration_minutes=90,
            subjects_label="পদার্থ",
        )
        db.add_all([paper_2024, paper_2023, ru_paper])
        db.flush()

        db.add_all(
            [
                _make_question(du, paper_2024, k_unit, physics, 1, "ভরবেগ দ্বিগুণ করা হলে গতিশক্তি কতগুণ হবে?", "If momentum is doubled, kinetic energy becomes?"),
                _make_question(du, paper_2024, k_unit, physics, 2, "সরল দোলকের দোলনকাল কত?", "Time period of a simple pendulum?"),
                _make_question(du, paper_2024, k_unit, chemistry, 3, "sp² সংকরায়ণ কোন যৌগে আছে?", "Which compound has sp2 hybridization?"),
                _make_question(du, paper_2024, k_unit, chemistry, 4, "NaOH-এর মোলার ভর কত?", "Molar mass of NaOH?", is_published=False),
                _make_question(du, paper_2023, k_unit, physics, 1, "শক্তির একক কী?", "Unit of energy?"),
                _make_question(du, paper_2023, k_unit, physics, 2, "আলোর বেগ কত?", "Speed of light?"),
                _make_question(ru, ru_paper, ru_unit, physics, 1, "রাজশাহী প্রশ্ন: শক্তির একক?", "RU question: unit of energy?"),
            ]
        )

        db.add(
            AdminUser(
                username="admin",
                password_hash=hash_password("admin-pass"),
                role="super_admin",
            )
        )
        db.commit()

    return {"du_key": du_key, "ru_key": ru_key}


@pytest.fixture()
def ctx():
    settings = Settings(
        _env_file=None,
        database_url="sqlite://",
        secret_key="test-secret-key",
        admin_session_secret="test-admin-secret",
        cors_origins="*",
        rate_limit_per_minute=100000,
        auth_rate_limit_per_minute=100000,
    )
    engine = create_db_engine(settings.database_url)
    with engine.begin() as connection:
        Base.metadata.create_all(connection)
        create_fts_schema(connection)

    session_factory = create_session_factory(engine)
    keys = _seed(session_factory)

    app = create_app(settings=settings, engine=engine)
    client = TestClient(app)

    return SimpleNamespace(
        app=app,
        client=client,
        engine=engine,
        session_factory=session_factory,
        settings=settings,
        du_key=keys["du_key"],
        ru_key=keys["ru_key"],
        du_headers={"X-App-Key": keys["du_key"]},
        ru_headers={"X-App-Key": keys["ru_key"]},
    )


def register_device(ctx, device_id: str = "device-0001") -> dict:
    response = ctx.client.post(
        "/api/v1/auth/device",
        json={"device_id": device_id, "display_name": "Test Student"},
        headers=ctx.du_headers,
    )
    assert response.status_code == 200, response.text
    token = response.json()["data"]["token"]
    return {"Authorization": "Bearer {token}".format(token=token)}

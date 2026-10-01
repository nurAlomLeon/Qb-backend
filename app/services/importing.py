from __future__ import annotations

import csv
import io
import json
from typing import Dict, List

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.content import Paper, Question, QuestionOption, Subject
from app.models.university import ContentMeta

OPTION_LETTERS = ["ক", "খ", "গ", "ঘ"]

LETTER_INDEX = {
    "ক": 0, "খ": 1, "গ": 2, "ঘ": 3,
    "A": 0, "B": 1, "C": 2, "D": 3,
    "a": 0, "b": 1, "c": 2, "d": 3,
    "0": 0, "1": 1, "2": 2, "3": 3,
}


def _cell(row: Dict, *names: str) -> str:
    for name in names:
        if name in row and row[name] is not None:
            value = str(row[name]).strip()
            if value:
                return value
    return ""


def parse_upload(filename: str, data: bytes) -> List[Dict]:
    lower = (filename or "").lower()
    if lower.endswith(".json"):
        payload = json.loads(data.decode("utf-8"))
        if isinstance(payload, dict) and "questions" in payload:
            payload = payload["questions"]
        return [dict(item) for item in payload]

    if lower.endswith(".xlsx"):
        from openpyxl import load_workbook

        workbook = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        sheet = workbook.active
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            return []
        headers = [
            str(value).strip() if value is not None else "" for value in rows[0]
        ]
        result: List[Dict] = []
        for row in rows[1:]:
            values = ["" if value is None else value for value in row]
            result.append(dict(zip(headers, values)))
        return result

    text = data.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    return [dict(row) for row in reader]


def import_rows(
    db: Session,
    paper: Paper,
    rows: List[Dict],
    default_subject_code: str = "",
) -> Dict:
    created = 0
    updated = 0
    skipped = 0
    errors: List[str] = []

    subjects = {
        subject.code: subject
        for subject in db.execute(select(Subject)).scalars().all()
    }

    for index, row in enumerate(rows, start=2):
        try:
            serial_raw = _cell(row, "serial", "question_no", "no")
            if not serial_raw:
                skipped += 1
                continue
            serial = int(float(serial_raw))

            subject_code = _cell(row, "subject_code", "subject") or default_subject_code
            subject = subjects.get(subject_code)
            if subject is None:
                errors.append(
                    "Row {row}: unknown subject '{code}'.".format(
                        row=index, code=subject_code or "-"
                    )
                )
                skipped += 1
                continue

            stem_bn = _cell(row, "stem_bn", "stem", "question_bn", "question")
            if not stem_bn:
                errors.append("Row {row}: missing question stem.".format(row=index))
                skipped += 1
                continue

            option_texts = [
                _cell(row, "option_a", "option_1", "a"),
                _cell(row, "option_b", "option_2", "b"),
                _cell(row, "option_c", "option_3", "c"),
                _cell(row, "option_d", "option_4", "d"),
            ]
            if not all(option_texts):
                options_json = _cell(row, "options")
                if options_json:
                    try:
                        option_texts = [
                            str(item) for item in json.loads(options_json)
                        ][:4]
                    except Exception:
                        pass
            if not all(option_texts):
                errors.append("Row {row}: needs 4 options.".format(row=index))
                skipped += 1
                continue

            correct_raw = _cell(row, "correct", "correct_letter", "answer")
            correct_index = LETTER_INDEX.get(correct_raw)
            if correct_index is None:
                try:
                    correct_index = int(float(correct_raw))
                except Exception:
                    correct_index = None
            if correct_index is None or not 0 <= correct_index <= 3:
                errors.append("Row {row}: invalid correct answer.".format(row=index))
                skipped += 1
                continue

            values = {
                "subject_id": subject.id,
                "chapter_bn": _cell(row, "chapter_bn", "chapter"),
                "stem_bn": stem_bn,
                "stem_en": _cell(row, "stem_en"),
                "correct_index": correct_index,
                "explanation_bn": _cell(row, "explanation_bn", "explanation"),
                "explanation_en": _cell(row, "explanation_en") or None,
                "shortcut_bn": _cell(row, "shortcut_bn", "shortcut") or None,
                "difficulty": _cell(row, "difficulty") or "medium",
            }

            existing = db.execute(
                select(Question).where(
                    Question.paper_id == paper.id,
                    Question.serial == serial,
                )
            ).scalar_one_or_none()

            if existing is None:
                question = Question(
                    university_id=paper.university_id,
                    paper_id=paper.id,
                    unit_id=paper.unit_id,
                    serial=serial,
                    **values,
                )
                db.add(question)
                db.flush()
                created += 1
            else:
                question = existing
                for key, value in values.items():
                    setattr(question, key, value)
                for option in list(question.options):
                    db.delete(option)
                db.flush()
                updated += 1

            for order, text in enumerate(option_texts):
                db.add(
                    QuestionOption(
                        question_id=question.id,
                        letter=OPTION_LETTERS[order],
                        text=text,
                        sort_order=order,
                    )
                )
        except Exception as exc:
            errors.append("Row {row}: {err}".format(row=index, err=exc))
            skipped += 1

    meta = db.execute(
        select(ContentMeta).where(
            ContentMeta.university_id == paper.university_id
        )
    ).scalar_one_or_none()
    if meta is None:
        db.add(ContentMeta(university_id=paper.university_id, content_version=1))
    else:
        meta.content_version += 1

    paper.question_count = (
        db.scalar(
            select(func.count(Question.id)).where(Question.paper_id == paper.id)
        )
        or 0
    )
    db.commit()

    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
    }

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, select  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.security import (  # noqa: E402
    generate_app_key,
    hash_app_key,
    hash_password,
)
from app.db.base import Base  # noqa: E402
from app.db.fts import create_fts_schema, rebuild_fts  # noqa: E402
from app.db.session import create_db_engine, create_session_factory  # noqa: E402
from app.models.admin import AdminUser  # noqa: E402
from app.models.content import (  # noqa: E402
    Paper,
    Question,
    QuestionOption,
    Subject,
    Unit,
)
from app.models.university import (  # noqa: E402
    AppConfig,
    AppKey,
    ContentMeta,
    University,
)
from app.utils.bengali import bn, superscript  # noqa: E402

LETTERS = ["ক", "খ", "গ", "ঘ"]

UNITS = [
    ("k", "ক", "ক ইউনিট", "বিজ্ঞান অনুষদ", "পদার্থ • রসায়ন • গণিত/জীববিজ্ঞান", 0),
    ("kh", "খ", "খ ইউনিট", "কলা ও সামাজিক বিজ্ঞান", "বাংলা • ইংরেজি • সাধারণ জ্ঞান", 1),
    ("g", "গ", "গ ইউনিট", "ব্যবসায় শিক্ষা অনুষদ", "হিসাববিজ্ঞান • ব্যবস্থাপনা • অর্থনীতি", 2),
    ("gh", "চ", "চ ইউনিট", "চারুকলা অনুষদ", "চিত্রাঙ্কন • ভাস্কর্য • ডিজাইন", 3),
]

SUBJECTS = [
    ("physics", "পদার্থবিজ্ঞান", "Physics", "science", "#2563EB", 0),
    ("chemistry", "রসায়ন", "Chemistry", "biotech", "#7C3AED", 1),
    ("math", "উচ্চতর গণিত", "Higher Math", "calculate", "#F59E0B", 2),
    ("biology", "জীববিজ্ঞান", "Biology", "eco", "#10B981", 3),
]

PAPERS = {
    "k": [
        (2024, "২০২৩-২৪ শিক্ষাবর্ষ", "fresh", 120, 90, "পদার্থ • রসায়ন • গণিত/জীববিজ্ঞান"),
        (2023, "২০২২-২৩ শিক্ষাবর্ষ", "attempted", 120, 90, "পূর্ণাঙ্গ প্রশ্ন ও নির্ভুল ব্যাখ্যা"),
        (2022, "২০২১-২২ শিক্ষাবর্ষ", "easy", 120, 90, "লিখিত ও বহুনির্বাচনী প্রশ্নসহ"),
        (2021, "২০২০-২১ শিক্ষাবর্ষ", "unsolved", 120, 90, "পূর্ণাঙ্গ প্রশ্ন ও নির্ভুল ব্যাখ্যা"),
        (2020, "২০১৯-২০ শিক্ষাবর্ষ", "full", 120, 90, "পূর্ণাঙ্গ প্রশ্ন ও নির্ভুল ব্যাখ্যা"),
        (2019, "২০১৮-১৯ শিক্ষাবর্ষ", "archive", 120, 90, "পূর্ণাঙ্গ প্রশ্ন ও নির্ভুল ব্যাখ্যা"),
    ],
    "kh": [
        (2024, "২০২৩-২৪ শিক্ষাবর্ষ", "fresh", 100, 90, "বাংলা • ইংরেজি • সাধারণ জ্ঞান"),
        (2023, "২০২২-২৩ শিক্ষাবর্ষ", "attempted", 100, 90, "পূর্ণাঙ্গ প্রশ্ন ও নির্ভুল ব্যাখ্যা"),
        (2022, "২০২১-২২ শিক্ষাবর্ষ", "easy", 100, 90, "সহজ ব্যাখ্যাসহ"),
    ],
    "g": [
        (2024, "২০২৩-২৪ শিক্ষাবর্ষ", "fresh", 100, 90, "হিসাববিজ্ঞান • ব্যবস্থাপনা • অর্থনীতি"),
        (2023, "২০২২-২৩ শিক্ষাবর্ষ", "unsolved", 100, 90, "পূর্ণাঙ্গ প্রশ্ন ও নির্ভুল ব্যাখ্যা"),
        (2022, "২০২১-২২ শিক্ষাবর্ষ", "archive", 100, 90, "পূর্ণাঙ্গ প্রশ্ন ও নির্ভুল ব্যাখ্যা"),
    ],
    "gh": [
        (2024, "২০২৩-২৪ শিক্ষাবর্ষ", "fresh", 60, 60, "চিত্রাঙ্কন • ভাস্কর্য • ডিজাইন"),
        (2023, "২০২২-২৩ শিক্ষাবর্ষ", "full", 60, 60, "পূর্ণাঙ্গ প্রশ্ন ও নির্ভুল ব্যাখ্যা"),
        (2022, "২০২১-২২ শিক্ষাবর্ষ", "archive", 60, 60, "পূর্ণাঙ্গ প্রশ্ন ও নির্ভুল ব্যাখ্যা"),
    ],
}


def _options(correct: str, wrongs: List[str], correct_index: int) -> List[tuple]:
    texts: List[str] = []
    wrong_index = 0
    for index in range(4):
        if index == correct_index:
            texts.append(correct)
        else:
            texts.append(wrongs[wrong_index])
            wrong_index += 1
    return [(LETTERS[i], texts[i], i) for i in range(4)]


def _physics(template: int, v: int) -> Dict:
    if template == 0:
        n = 2 + v
        return {
            "chapter_bn": "১ম পত্র • অধ্যায় ৪",
            "stem_bn": "একটি সরল দোলকের দোলনকাল {n} গুণ করতে হলে এর কার্যকরী দৈর্ঘ্য কত গুণ বাড়াতে হবে?".format(n=bn(n)),
            "stem_en": "To make the time period of a simple pendulum {n} times, by how many times must its effective length be increased?".format(n=n),
            "correct": "{value} গুণ".format(value=bn(n * n)),
            "wrongs": [
                "{value} গুণ".format(value=bn(n)),
                "{value} গুণ".format(value=bn(n + 3)),
                "{value} গুণ".format(value=bn(n * n + 4)),
            ],
            "explanation": "আমরা জানি সরল দোলকের সূত্র: T = 2π√(L/g) ⇒ T ∝ √L বা L ∝ T²। অতএব দোলনকাল {n} গুণ করলে কার্যকরী দৈর্ঘ্য ({n})² = {ns} গুণ হবে।".format(n=bn(n), ns=bn(n * n)),
            "shortcut": "T ∝ √L (g স্থির থাকলে)",
        }
    if template == 1:
        n = 2 + v
        return {
            "chapter_bn": "১ম পত্র • অধ্যায় ৩",
            "stem_bn": "একটি গতিশীল কণার ভরবেগ {n} গুণ করা হলে তার গতিশক্তি কতগুণ হবে?".format(n=bn(n)),
            "stem_en": "If the momentum of a moving particle is increased {n} times, how many times will its kinetic energy become?".format(n=n),
            "correct": "{value} গুণ".format(value=bn(n * n)),
            "wrongs": [
                "{value} গুণ".format(value=bn(n)),
                "{value} গুণ".format(value=bn(n + 1)),
                "{value} গুণ".format(value=bn(n * n * n)),
            ],
            "explanation": "গতিশক্তি Ek = p²/2m, যেখানে p হলো ভরবেগ এবং m কণার ভর। ভর স্থির থাকলে Ek ∝ p²। সুতরাং ভরবেগ {n} গুণ করলে গতিশক্তি ({n})² = {ns} গুণ হয়।".format(n=bn(n), ns=bn(n * n)),
            "shortcut": "Ek ∝ p² (ভর স্থির থাকলে)",
        }
    n = 2 + v
    return {
        "chapter_bn": "১ম পত্র • অধ্যায় ৩",
        "stem_bn": "কোনো বস্তুর বেগ {n} গুণ করা হলে তার গতিশক্তি কতগুণ হবে?".format(n=bn(n)),
        "stem_en": "If the velocity of a body is increased {n} times, how many times will its kinetic energy become?".format(n=n),
        "correct": "{value} গুণ".format(value=bn(n * n)),
        "wrongs": [
            "{value} গুণ".format(value=bn(n)),
            "{value} গুণ".format(value=bn(n + 3)),
            "{value} গুণ".format(value=bn(n * n + 2)),
        ],
        "explanation": "গতিশক্তি Ek = ½mv² ⇒ Ek ∝ v²। সুতরাং বেগ {n} গুণ করলে গতিশক্তি ({n})² = {ns} গুণ হবে।".format(n=bn(n), ns=bn(n * n)),
        "shortcut": "Ek ∝ v²",
    }


def _chemistry(template: int, v: int) -> Dict:
    if template == 0:
        kind = v % 3
        if kind == 0:
            return {
                "chapter_bn": "২য় পত্র • অধ্যায় ২",
                "stem_bn": "নিচের কোন যৌগে sp² সংকরায়ণ (Hybridization) উপস্থিত রয়েছে?",
                "stem_en": "Which of the following compounds contains sp² hybridization?",
                "correct": "C₂H₄ (ইথিন)",
                "wrongs": ["C₂H₆ (ইথেন)", "C₂H₂ (ইথাইন)", "CH₄ (মিথেন)"],
                "explanation": "ইথিনে (CH₂=CH₂) প্রতিটি কার্বন তিনটি σ বন্ধন ও একটি π বন্ধন গঠন করে, তাই এটি sp² সংকরিত। C₂H₆ হলো sp³, C₂H₂ হলো sp এবং CH₄ হলো sp³ সংকরায়ণ।",
                "shortcut": None,
            }
        if kind == 1:
            return {
                "chapter_bn": "২য় পত্র • অধ্যায় ২",
                "stem_bn": "নিচের কোন যৌগে sp³ সংকরায়ণ (Hybridization) উপস্থিত রয়েছে?",
                "stem_en": "Which of the following compounds contains sp³ hybridization?",
                "correct": "CH₄ (মিথেন)",
                "wrongs": ["C₂H₄ (ইথিন)", "C₂H₂ (ইথাইন)", "CO₂ (কার্বন ডাই-অক্সাইড)"],
                "explanation": "মিথেনে (CH₄) কার্বন চারটি σ বন্ধন গঠন করে, তাই এটি sp³ সংকরিত। C₂H₄ হলো sp², C₂H₂ ও CO₂ হলো sp সংকরায়ণ।",
                "shortcut": None,
            }
        return {
            "chapter_bn": "২য় পত্র • অধ্যায় ২",
            "stem_bn": "নিচের কোন যৌগে sp সংকরায়ণ (Hybridization) উপস্থিত রয়েছে?",
            "stem_en": "Which of the following compounds contains sp hybridization?",
            "correct": "C₂H₂ (ইথাইন)",
            "wrongs": ["C₂H₄ (ইথিন)", "CH₄ (মিথেন)", "BF₃ (বোরন ট্রাইফ্লোরাইড)"],
            "explanation": "ইথাইনে (HC≡CH) প্রতিটি কার্বন দুটি σ ও দুটি π বন্ধন গঠন করে, তাই এটি sp সংকরিত। C₂H₄ হলো sp², CH₄ হলো sp³ এবং BF₃ হলো sp² সংকরায়ণ।",
            "shortcut": None,
        }
    if template == 1:
        p = 3 + v
        return {
            "chapter_bn": "১ম পত্র • অধ্যায় ৫",
            "stem_bn": "একটি দ্রবণের pH = {p} হলে দ্রবণটির [H⁺] কত mol/L?".format(p=bn(p)),
            "stem_en": "If the pH of a solution is {p}, what is the [H⁺] of the solution in mol/L?".format(p=p),
            "correct": "10⁻{sup} mol/L".format(sup=superscript(p)),
            "wrongs": [
                "10⁻{sup} mol/L".format(sup=superscript(p + 1)),
                "10⁻{sup} mol/L".format(sup=superscript(p - 1)),
                "{p} mol/L".format(p=bn(p)),
            ],
            "explanation": "pH = −log[H⁺] ⇒ [H⁺] = 10^(−pH) = 10⁻{sup} mol/L।".format(sup=superscript(p)),
            "shortcut": None,
        }
    n = 1 + v
    return {
        "chapter_bn": "১ম পত্র • অধ্যায় ৪",
        "stem_bn": "{n} mol NaOH-এর ভর কত গ্রাম? (NaOH-এর মোলার ভর = 40 g/mol)".format(n=bn(n)),
        "stem_en": "What is the mass of {n} mol NaOH in grams? (Molar mass of NaOH = 40 g/mol)".format(n=n),
        "correct": "{value} g".format(value=bn(40 * n)),
        "wrongs": [
            "{value} g".format(value=bn(40 + n)),
            "{value} g".format(value=bn(20 * n)),
            "{value} g".format(value=bn(40 * n + 40)),
        ],
        "explanation": "ভর = মোল সংখ্যা × মোলার ভর = {n} × 40 = {value} g।".format(n=bn(n), value=bn(40 * n)),
        "shortcut": None,
    }


def _math(template: int, v: int) -> Dict:
    if template == 0:
        a = 5 + v
        b = 3 + v
        return {
            "chapter_bn": "১ম পত্র • অধ্যায় ৯",
            "stem_bn": "lim(x→0) (sin {a}x / tan {b}x) এর মান কত?".format(a=bn(a), b=bn(b)),
            "stem_en": "What is the value of lim(x→0) (sin {a}x / tan {b}x)?".format(a=a, b=b),
            "correct": "{a}/{b}".format(a=bn(a), b=bn(b)),
            "wrongs": ["{b}/{a}".format(a=bn(a), b=bn(b)), "০", "১"],
            "explanation": "ল'হসপিটাল নিয়ম অথবা স্ট্যান্ডার্ড লিমিট সূত্র প্রয়োগ করে: lim (sin ax / tan bx) = a/b = {a}/{b}।".format(a=bn(a), b=bn(b)),
            "shortcut": None,
        }
    if template == 1:
        n = 3 + v
        return {
            "chapter_bn": "১ম পত্র • অধ্যায় ৯",
            "stem_bn": "d/dx (x{sup}) এর মান কত?".format(sup=superscript(n)),
            "stem_en": "What is the value of d/dx (x^{n})?".format(n=n),
            "correct": "{n}x{sup}".format(n=bn(n), sup=superscript(n - 1)),
            "wrongs": [
                "x{sup}".format(sup=superscript(n + 1)),
                "{n}x{sup}".format(n=bn(n), sup=superscript(n)),
                "x{sup}".format(sup=superscript(n)),
            ],
            "explanation": "ঘাতের অন্তরজ সূত্র: d/dx (xⁿ) = n·xⁿ⁻¹। এখানে n = {n}, তাই উত্তর {n}x{sup}।".format(n=bn(n), sup=superscript(n - 1)),
            "shortcut": None,
        }
    n = 5 + v
    total = (n * (3 * n + 1)) // 2
    return {
        "chapter_bn": "১ম পত্র • অধ্যায় ৬",
        "stem_bn": "একটি সমান্তর প্রগমনে প্রথম পদ ২ ও সাধারণ অন্তর ৩ হলে প্রথম {n} পদের সমষ্টি কত?".format(n=bn(n)),
        "stem_en": "In an arithmetic progression with first term 2 and common difference 3, what is the sum of the first {n} terms?".format(n=n),
        "correct": bn(total),
        "wrongs": [bn(total + n), bn(total - n), bn(total + 2 * n)],
        "explanation": "Sn = n/2 [2a + (n−1)d] = {n}/2 × [4 + {d}] = {total}।".format(n=bn(n), d=bn(3 * (n - 1)), total=bn(total)),
        "shortcut": None,
    }


def _biology(template: int, v: int) -> Dict:
    if template == 0:
        return {
            "chapter_bn": "১ম পত্র • অধ্যায় ১",
            "stem_bn": "ডিএনএ (DNA) অণুর ডাবল হেলিক্স কাঠামোর ব্যাস কত?",
            "stem_en": "What is the diameter of the DNA double helix structure?",
            "correct": "20 Å",
            "wrongs": ["34 Å", "3.4 Å", "10 Å"],
            "explanation": "ওয়াটসন ও ক্রিক মডেল অনুসারে DNA ডাবল হেলিক্সের ব্যাস 20 Å (বা 2 nm) এবং একটি পূর্ণ প্যাঁচের দৈর্ঘ্য 34 Å, যাতে ১০ জোড়া নিউক্লিওটাইড থাকে।",
            "shortcut": None,
        }
    if template == 1:
        kind = v % 4
        if kind == 0:
            return {
                "chapter_bn": "১ম পত্র • অধ্যায় ১",
                "stem_bn": "কোষের কোন অঙ্গাণুতে প্রোটিন সংশ্লেষণ ঘটে?",
                "stem_en": "In which organelle of the cell does protein synthesis occur?",
                "correct": "রাইবোজোম",
                "wrongs": ["মাইটোকন্ড্রিয়া", "নিউক্লিয়াস", "গলগি বস্তু"],
                "explanation": "রাইবোজোমকে কোষের প্রোটিন ফ্যাক্টরি বলা হয়; এখানেই mRNA-এর নির্দেশনা অনুযায়ী অ্যামিনো অ্যাসিড যুক্ত হয়ে প্রোটিন তৈরি হয়।",
                "shortcut": None,
            }
        if kind == 1:
            return {
                "chapter_bn": "১ম পত্র • অধ্যায় ১",
                "stem_bn": "কোষের শক্তিঘর (Powerhouse of the cell) কোনটি?",
                "stem_en": "Which organelle is called the powerhouse of the cell?",
                "correct": "মাইটোকন্ড্রিয়া",
                "wrongs": ["রাইবোজোম", "ক্লোরোপ্লাস্ট", "নিউক্লিয়াস"],
                "explanation": "মাইটোকন্ড্রিয়ায় শ্বসন প্রক্রিয়ার মাধ্যমে ATP উৎপন্ন হয়, তাই একে কোষের শক্তিঘর বলা হয়।",
                "shortcut": None,
            }
        if kind == 2:
            return {
                "chapter_bn": "১ম পত্র • অধ্যায় ১",
                "stem_bn": "কোষের নিয়ন্ত্রণ কেন্দ্র কোনটি?",
                "stem_en": "Which is the control center of the cell?",
                "correct": "নিউক্লিয়াস",
                "wrongs": ["সাইটোপ্লাজম", "রাইবোজোম", "মাইটোকন্ড্রিয়া"],
                "explanation": "নিউক্লিয়াসে DNA থাকে এবং এটি কোষের সমস্ত কার্যক্রম নিয়ন্ত্রণ করে, তাই একে কোষের নিয়ন্ত্রণ কেন্দ্র বলা হয়।",
                "shortcut": None,
            }
        return {
            "chapter_bn": "১ম পত্র • অধ্যায় ১",
            "stem_bn": "সালোকসংশ্লেষণ (Photosynthesis) কোষের কোথায় ঘটে?",
            "stem_en": "Where in the cell does photosynthesis take place?",
            "correct": "ক্লোরোপ্লাস্ট",
            "wrongs": ["মাইটোকন্ড্রিয়া", "রাইবোজোম", "ভ্যাকুওল"],
            "explanation": "ক্লোরোপ্লাস্টে ক্লোরোফিল থাকে, যা আলোকশক্তি শোষণ করে সালোকসংশ্লেষণ প্রক্রিয়ায় শর্করা তৈরি করে।",
            "shortcut": None,
        }
    kind = v % 2
    if kind == 0:
        return {
            "chapter_bn": "২য় পত্র • অধ্যায় ২",
            "stem_bn": "মানবদেহে ইনসুলিন কোথায় তৈরি হয়?",
            "stem_en": "Where is insulin produced in the human body?",
            "correct": "অগ্ন্যাশয়ের আইলেটস অব ল্যাঙ্গারহ্যান্স",
            "wrongs": ["যকৃত", "বৃক্ক", "পিটুইটারি গ্রন্থি"],
            "explanation": "অগ্ন্যাশয়ের আইলেটস অব ল্যাঙ্গারহ্যান্সের বিটা কোষে ইনসুলিন তৈরি হয়, যা রক্তের গ্লুকোজ নিয়ন্ত্রণ করে।",
            "shortcut": None,
        }
    return {
        "chapter_bn": "১ম পত্র • অধ্যায় ১",
        "stem_bn": "ডিএনএ-তে নাইট্রোজেন বেস কতটি প্রকার?",
        "stem_en": "How many types of nitrogenous bases are there in DNA?",
        "correct": "৪টি",
        "wrongs": ["২টি", "৩টি", "৫টি"],
        "explanation": "DNA-তে চারটি নাইট্রোজেন বেস থাকে: অ্যাডেনিন (A), গুয়ানিন (G), সাইটোসিন (C) ও থাইমিন (T)।",
        "shortcut": None,
    }


_DRAFT_BUILDERS = [_physics, _chemistry, _math, _biology]
_DIFFICULTIES = ["easy", "medium", "hard"]


def build_questions(paper: Paper, subject_rows: List[Subject]) -> List[Question]:
    per_subject = paper.question_count // 4
    questions: List[Question] = []
    for subject_index, subject in enumerate(subject_rows):
        for i in range(per_subject):
            template = (i * 3) // per_subject
            variation = i % 10
            serial = subject_index * per_subject + i + 1
            draft = _DRAFT_BUILDERS[subject_index](template, variation)
            correct_index = (variation + template) % 4
            analytics_percent = 55 + ((variation * 7 + subject_index * 13 + serial) % 40)

            question = Question(
                university_id=paper.university_id,
                paper_id=paper.id,
                unit_id=paper.unit_id,
                subject_id=subject.id,
                serial=serial,
                chapter_bn=draft["chapter_bn"],
                stem_bn=draft["stem_bn"],
                stem_en=draft["stem_en"],
                correct_index=correct_index,
                explanation_bn=draft["explanation"],
                shortcut_bn=draft["shortcut"],
                difficulty=_DIFFICULTIES[variation % 3],
                analytics_percent=analytics_percent,
                analytics_attempts=100,
                analytics_correct=analytics_percent,
                is_published=True,
            )
            for letter, text, order in _options(
                draft["correct"], draft["wrongs"], correct_index
            ):
                question.options.append(
                    QuestionOption(letter=letter, text=text, sort_order=order)
                )
            questions.append(question)
    return questions


def seed(args: argparse.Namespace) -> None:
    settings = get_settings()
    database_url = args.database_url or settings.database_url
    engine = create_db_engine(database_url)
    session_factory = create_session_factory(engine)

    with engine.begin() as connection:
        if args.reset:
            Base.metadata.drop_all(connection)
        Base.metadata.create_all(connection)
        create_fts_schema(connection)

    with session_factory() as db:
        university = db.execute(
            select(University).where(University.slug == args.university_slug)
        ).scalar_one_or_none()
        if university is None:
            university = University(
                slug=args.university_slug,
                name_bn=args.university_name_bn,
                name_en=args.university_name_en,
                logo_url=None,
                theme={"primary": "#1E3A8A", "background": "#F8FAFC"},
            )
            db.add(university)
            db.flush()

        if db.execute(
            select(AppConfig).where(AppConfig.university_id == university.id)
        ).scalar_one_or_none() is None:
            db.add(
                AppConfig(
                    university_id=university.id,
                    min_app_version="2.4.0",
                    latest_app_version="2.4.0",
                    force_update=False,
                    sync_message="সার্ভার সিঙ্ক ও ডেটা ভেরিফিকেশন সক্রিয়",
                )
            )

        meta = db.execute(
            select(ContentMeta).where(ContentMeta.university_id == university.id)
        ).scalar_one_or_none()
        if meta is None:
            meta = ContentMeta(university_id=university.id, content_version=1)
            db.add(meta)

        subject_rows: List[Subject] = []
        for code, label_bn, label_en, icon, color, order in SUBJECTS:
            subject = db.execute(
                select(Subject).where(Subject.code == code)
            ).scalar_one_or_none()
            if subject is None:
                subject = Subject(
                    code=code,
                    label_bn=label_bn,
                    label_en=label_en,
                    icon=icon,
                    color=color,
                    sort_order=order,
                )
                db.add(subject)
                db.flush()
            subject_rows.append(subject)

        units_by_code: Dict[str, Unit] = {}
        for unit_code, letter, title, faculty, subjects_label, order in UNITS:
            unit = db.execute(
                select(Unit).where(
                    Unit.university_id == university.id,
                    Unit.letter == letter,
                )
            ).scalar_one_or_none()
            if unit is None:
                unit = Unit(
                    university_id=university.id,
                    letter=letter,
                    title_bn=title,
                    faculty_bn=faculty,
                    subjects_label=subjects_label,
                    sort_order=order,
                )
                db.add(unit)
                db.flush()
            units_by_code[unit_code] = unit

        db.commit()

        created_questions = 0
        for unit_code, unit_papers in PAPERS.items():
            unit = units_by_code[unit_code]
            for year, label, status, question_count, duration, subjects_label in unit_papers:
                paper = db.execute(
                    select(Paper).where(
                        Paper.unit_id == unit.id,
                        Paper.year == year,
                    )
                ).scalar_one_or_none()
                if paper is None:
                    paper = Paper(
                        university_id=university.id,
                        unit_id=unit.id,
                        year=year,
                        label_bn=label,
                        status=status,
                        question_count=question_count,
                        duration_minutes=duration,
                        subjects_label=subjects_label,
                    )
                    db.add(paper)
                    db.flush()

                db.execute(delete(Question).where(Question.paper_id == paper.id))
                db.flush()

                questions = build_questions(paper, subject_rows)
                db.add_all(questions)
                db.flush()
                created_questions += len(questions)
                print(
                    "Seeded {count} questions for {unit} {year}.".format(
                        count=len(questions), unit=unit.title_bn, year=paper.label_bn
                    )
                )

        raw_key = generate_app_key()
        db.add(
            AppKey(
                university_id=university.id,
                key_hash=hash_app_key(raw_key),
                label=args.app_key_label,
            )
        )

        if args.admin_username and args.admin_password:
            admin = db.execute(
                select(AdminUser).where(AdminUser.username == args.admin_username)
            ).scalar_one_or_none()
            if admin is None:
                db.add(
                    AdminUser(
                        username=args.admin_username,
                        password_hash=hash_password(args.admin_password),
                        role="super_admin",
                    )
                )

        db.commit()

        with engine.begin() as connection:
            rebuild_fts(connection)

        print("")
        print("University : {slug} ({name})".format(slug=university.slug, name=university.name_bn))
        print("Questions  : {count}".format(count=created_questions))
        print("App key    : {key}".format(key=raw_key))
        if args.admin_username and args.admin_password:
            print("Admin user : {user}".format(user=args.admin_username))


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo content.")
    parser.add_argument("--database-url", default=None)
    parser.add_argument("--university-slug", default="du")
    parser.add_argument("--university-name-bn", default="ঢাকা বিশ্ববিদ্যালয়")
    parser.add_argument("--university-name-en", default="University of Dhaka")
    parser.add_argument("--app-key-label", default="production")
    parser.add_argument("--admin-username", default=None)
    parser.add_argument("--admin-password", default=None)
    parser.add_argument("--reset", action="store_true")
    seed(parser.parse_args())


if __name__ == "__main__":
    main()

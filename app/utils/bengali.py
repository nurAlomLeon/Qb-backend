from __future__ import annotations

_DIGITS = ["০", "১", "২", "৩", "৪", "৫", "৬", "৭", "৮", "৯"]

_SUPERSCRIPTS = {
    "0": "⁰",
    "1": "¹",
    "2": "²",
    "3": "³",
    "4": "⁴",
    "5": "⁵",
    "6": "⁶",
    "7": "⁷",
    "8": "⁸",
    "9": "⁹",
}


def bn(value: object) -> str:
    return "".join(_DIGITS[int(ch)] if ch.isdigit() else ch for ch in str(value))


def superscript(value: object) -> str:
    return "".join(_SUPERSCRIPTS.get(ch, ch) for ch in str(value))


def clock(total_seconds: int) -> str:
    minutes = f"{total_seconds // 60:02d}"
    seconds = f"{total_seconds % 60:02d}"
    return f"{bn(minutes)}:{bn(seconds)}"

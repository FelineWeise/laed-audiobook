from __future__ import annotations

from enum import Enum


class Language(str, Enum):
    en = "en"
    de = "de"


LANGUAGE_LABELS: dict[Language, str] = {
    Language.en: "English",
    Language.de: "German (Hochdeutsch)",
}


def language_label(language: Language) -> str:
    return LANGUAGE_LABELS[language]

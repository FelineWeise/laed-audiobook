from __future__ import annotations

from enum import Enum
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from audiobook.language import Language, language_label


class Mode(str, Enum):
    review = "review"
    balanced = "balanced"
    narrative = "narrative"


_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def render_mode_prompt(
    mode: Mode,
    source_text: str,
    title: str | None = None,
    *,
    part_index: int = 1,
    part_count: int = 1,
    prior_ending: str = "",
    language: Language = Language.en,
) -> str:
    env = Environment(
        loader=FileSystemLoader(str(_PROMPTS_DIR)),
        autoescape=select_autoescape(enabled_extensions=()),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template(f"{mode.value}.jinja")
    return template.render(
        title=title or "Document",
        source_text=source_text,
        part_index=part_index,
        part_count=part_count,
        prior_ending=prior_ending,
        is_continuation=bool(prior_ending) and part_index > 1,
        language=language.value,
        language_label=language_label(language),
    )


def render_translate_prompt(
    source_text: str,
    title: str | None = None,
    *,
    part_index: int = 1,
    part_count: int = 1,
    prior_ending: str = "",
    language: Language = Language.de,
) -> str:
    env = Environment(
        loader=FileSystemLoader(str(_PROMPTS_DIR)),
        autoescape=select_autoescape(enabled_extensions=()),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("translate_document.jinja")
    return template.render(
        title=title or "Document",
        source_text=source_text,
        part_index=part_index,
        part_count=part_count,
        prior_ending=prior_ending,
        is_continuation=bool(prior_ending) and part_index > 1,
        language=language.value,
        language_label=language_label(language),
    )

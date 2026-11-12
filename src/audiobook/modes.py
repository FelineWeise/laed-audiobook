from __future__ import annotations

from enum import Enum
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


class Mode(str, Enum):
    review = "review"
    balanced = "balanced"
    narrative = "narrative"


_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def render_mode_prompt(mode: Mode, source_text: str, title: str | None = None) -> str:
    env = Environment(
        loader=FileSystemLoader(str(_PROMPTS_DIR)),
        autoescape=select_autoescape(enabled_extensions=()),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template(f"{mode.value}.jinja")
    return template.render(title=title or "Document", source_text=source_text)

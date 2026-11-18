from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional

import typer

from audiobook.config import Settings
from audiobook.extract import extract_clipboard, extract_path
from audiobook.language import Language
from audiobook.modes import Mode
from audiobook.pace import Pace, speed_for_pace
from audiobook.pipeline import run_pipeline, translate_document

app = typer.Typer(
    name="audiobook",
    help="Turn documents or clipboard text into a stitched MP3 via llm-gateway Kokoro.",
    no_args_is_help=True,
)


def _settings() -> Settings:
    return Settings()


def _apply_voice_pace_lang(
    settings: Settings,
    *,
    voice: str | None,
    pace: Pace | None,
    language: Language | None,
) -> None:
    if voice:
        settings.tts_voice = voice
    if pace is not None:
        settings.tts_speed = speed_for_pace(pace)
    if language is not None:
        settings.language = language.value


@app.command("file")
def from_file(
    path: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    mode: Mode = typer.Option(Mode.balanced, "--mode", "-m"),
    pace: Pace = typer.Option(
        Pace.normal,
        "--pace",
        "-p",
        help="Narration speed: slow (0.85), normal (1.0), fast (1.15).",
    ),
    language: Language = typer.Option(
        Language.en,
        "--lang",
        "-l",
        help="Spoken script language: en or de.",
    ),
    raw: bool = typer.Option(
        False,
        "--raw",
        help="Skip chat rewrite; speak extracted text directly.",
    ),
    out: Optional[Path] = typer.Option(None, "--out", "-o", help="Output MP3 path."),
    voice: Optional[str] = typer.Option(None, "--voice"),
) -> None:
    """Extract a file, rewrite for a mode, synthesize, write Desktop MP3."""
    settings = _settings()
    _apply_voice_pace_lang(settings, voice=voice, pace=pace, language=language)
    text = extract_path(path)
    result = run_pipeline(
        source_text=text,
        mode=mode,
        settings=settings,
        title=path.stem,
        raw=raw,
        out=out,
        language=language,
    )
    typer.echo(str(result))


@app.command("clipboard")
def from_clipboard(
    mode: Mode = typer.Option(Mode.review, "--mode", "-m"),
    pace: Pace = typer.Option(Pace.normal, "--pace", "-p"),
    language: Language = typer.Option(Language.en, "--lang", "-l"),
    raw: bool = typer.Option(False, "--raw"),
    out: Optional[Path] = typer.Option(None, "--out", "-o"),
    voice: Optional[str] = typer.Option(None, "--voice"),
) -> None:
    """Read macOS clipboard (pbpaste), rewrite, synthesize, write Desktop MP3."""
    settings = _settings()
    _apply_voice_pace_lang(settings, voice=voice, pace=pace, language=language)
    pasted = subprocess.check_output(["pbpaste"], text=True)
    text = extract_clipboard(pasted)
    result = run_pipeline(
        source_text=text,
        mode=mode,
        settings=settings,
        title="clipboard",
        raw=raw,
        out=out,
        language=language,
    )
    typer.echo(str(result))


@app.command("text")
def from_text(
    body: str = typer.Argument(..., help="Inline text to speak."),
    mode: Mode = typer.Option(Mode.review, "--mode", "-m"),
    pace: Pace = typer.Option(Pace.normal, "--pace", "-p"),
    language: Language = typer.Option(Language.en, "--lang", "-l"),
    raw: bool = typer.Option(False, "--raw"),
    out: Optional[Path] = typer.Option(None, "--out", "-o"),
    voice: Optional[str] = typer.Option(None, "--voice"),
) -> None:
    """Speak a short inline string (useful for smoke tests)."""
    settings = _settings()
    _apply_voice_pace_lang(settings, voice=voice, pace=pace, language=language)
    result = run_pipeline(
        source_text=body,
        mode=mode,
        settings=settings,
        title="text",
        raw=raw,
        out=out,
        language=language,
    )
    typer.echo(str(result))


@app.command("translate")
def translate_file(
    path: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    language: Language = typer.Option(
        Language.de,
        "--lang",
        "-l",
        help="Target written language (default: de).",
    ),
    out: Optional[Path] = typer.Option(
        None,
        "--out",
        "-o",
        help="Output Markdown path.",
    ),
) -> None:
    """Rewrite a document into a written Markdown file in the target language."""
    settings = _settings()
    text = extract_path(path)
    result = translate_document(
        source_text=text,
        settings=settings,
        title=path.stem,
        language=language,
        out=out,
    )
    typer.echo(str(result))


if __name__ == "__main__":
    app()

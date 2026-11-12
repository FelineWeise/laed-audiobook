from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional

import typer

from audiobook.config import Settings
from audiobook.extract import extract_clipboard, extract_path
from audiobook.modes import Mode
from audiobook.pipeline import run_pipeline

app = typer.Typer(
    name="audiobook",
    help="Turn documents or clipboard text into a stitched MP3 via llm-gateway Kokoro.",
    no_args_is_help=True,
)


def _settings() -> Settings:
    return Settings()


@app.command("file")
def from_file(
    path: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    mode: Mode = typer.Option(Mode.balanced, "--mode", "-m"),
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
    if voice:
        settings.tts_voice = voice
    text = extract_path(path)
    result = run_pipeline(
        source_text=text,
        mode=mode,
        settings=settings,
        title=path.stem,
        raw=raw,
        out=out,
    )
    typer.echo(str(result))


@app.command("clipboard")
def from_clipboard(
    mode: Mode = typer.Option(Mode.review, "--mode", "-m"),
    raw: bool = typer.Option(False, "--raw"),
    out: Optional[Path] = typer.Option(None, "--out", "-o"),
    voice: Optional[str] = typer.Option(None, "--voice"),
) -> None:
    """Read macOS clipboard (pbpaste), rewrite, synthesize, write Desktop MP3."""
    settings = _settings()
    if voice:
        settings.tts_voice = voice
    pasted = subprocess.check_output(["pbpaste"], text=True)
    text = extract_clipboard(pasted)
    result = run_pipeline(
        source_text=text,
        mode=mode,
        settings=settings,
        title="clipboard",
        raw=raw,
        out=out,
    )
    typer.echo(str(result))


@app.command("text")
def from_text(
    body: str = typer.Argument(..., help="Inline text to speak."),
    mode: Mode = typer.Option(Mode.review, "--mode", "-m"),
    raw: bool = typer.Option(False, "--raw"),
    out: Optional[Path] = typer.Option(None, "--out", "-o"),
    voice: Optional[str] = typer.Option(None, "--voice"),
) -> None:
    """Speak a short inline string (useful for smoke tests)."""
    settings = _settings()
    if voice:
        settings.tts_voice = voice
    result = run_pipeline(
        source_text=body,
        mode=mode,
        settings=settings,
        title="text",
        raw=raw,
        out=out,
    )
    typer.echo(str(result))


if __name__ == "__main__":
    app()

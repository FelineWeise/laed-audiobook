from __future__ import annotations

import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from audiobook.chunk import chunk_script, with_bridge_context
from audiobook.config import Settings
from audiobook.gateway import GatewayClient
from audiobook.modes import Mode, render_mode_prompt
from audiobook.stitch import stitch_mp3_segments


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return slug[:48] or "audiobook"


def run_pipeline(
    *,
    source_text: str,
    mode: Mode,
    settings: Settings,
    title: str | None = None,
    raw: bool = False,
    out: Path | None = None,
) -> Path:
    """Rewrite (unless raw), chunk, TTS, stitch → Desktop MP3."""
    display_title = title or "document"
    if raw:
        script = source_text.strip()
    else:
        prompt = render_mode_prompt(mode, source_text, title=display_title)
        with GatewayClient(settings) as gateway:
            script = gateway.chat_completion(model=settings.chat_model, user_prompt=prompt)

    chunks = chunk_script(script, max_words=settings.chunk_max_words)
    if not chunks:
        raise ValueError("Nothing to speak after processing.")
    speak_chunks = with_bridge_context(chunks) if not raw else chunks

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    output_path = out or (
        settings.output_dir / f"audiobook-{_slug(display_title)}-{mode.value}-{stamp}.mp3"
    )

    with tempfile.TemporaryDirectory(prefix="audiobook-seg-") as tmp:
        tmp_dir = Path(tmp)
        segment_paths: list[Path] = []
        with GatewayClient(settings) as gateway:
            for index, text in enumerate(speak_chunks):
                audio = gateway.speech(
                    model=settings.tts_model,
                    text=text,
                    voice=settings.tts_voice,
                    speed=settings.tts_speed,
                )
                path = tmp_dir / f"seg-{index:04d}.mp3"
                path.write_bytes(audio)
                segment_paths.append(path)
        stitch_mp3_segments(segment_paths, output_path)
    return output_path

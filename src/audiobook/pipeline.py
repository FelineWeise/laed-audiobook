from __future__ import annotations

import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from audiobook.chunk import chunk_script, dedupe_seam_sentences, last_sentences
from audiobook.config import Settings
from audiobook.gateway import GatewayClient
from audiobook.language import Language, language_label
from audiobook.modes import Mode, render_mode_prompt, render_translate_prompt
from audiobook.section import split_source_sections
from audiobook.stitch import stitch_mp3_segments


def _parse_language(value: str | Language) -> Language:
    if isinstance(value, Language):
        return value
    return Language(value)


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return slug[:48] or "audiobook"


def _log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def _spoken_system_prompt(language: Language) -> str:
    return (
        f"You write spoken scripts in {language_label(language)} for text-to-speech. "
        "Return only the script body."
    )


def _rewrite_section(
    settings: Settings,
    mode: Mode,
    title: str,
    section_index: int,
    section_count: int,
    section_text: str,
    prior_ending: str,
    language: Language,
) -> str:
    prompt = render_mode_prompt(
        mode,
        section_text,
        title=title,
        part_index=section_index + 1,
        part_count=section_count,
        prior_ending=prior_ending,
        language=language,
    )
    with GatewayClient(settings) as gateway:
        return gateway.chat_completion(
            model=settings.chat_model,
            user_prompt=prompt,
            system_prompt=_spoken_system_prompt(language),
        )


def _build_script(
    *,
    source_text: str,
    mode: Mode,
    settings: Settings,
    title: str,
    language: Language,
) -> str:
    sections = split_source_sections(
        source_text,
        max_chars=settings.section_max_chars,
        overlap_chars=settings.section_overlap_chars,
    )
    if not sections:
        raise ValueError("Nothing to rewrite.")
    _log(
        f"rewrite: {len(sections)} section(s) sequential, "
        f"lang={language.value}, overlap={settings.section_overlap_chars}, "
        f"model={settings.chat_model}"
    )

    scripts: list[str] = []
    prior_ending = ""
    for index, section in enumerate(sections):
        script = _rewrite_section(
            settings,
            mode,
            title,
            index,
            len(sections),
            section,
            prior_ending,
            language,
        )
        scripts.append(script)
        prior_ending = last_sentences(script, count=2)
        _log(f"rewrite: completed {index + 1}/{len(sections)}")

    joined = "\n\n".join(scripts).strip()
    return dedupe_seam_sentences(joined)


def translate_document(
    *,
    source_text: str,
    settings: Settings,
    title: str | None = None,
    language: Language | str = Language.de,
    out: Path | None = None,
) -> Path:
    """Rewrite the full source into a written document in the target language."""
    lang = _parse_language(language)
    display_title = title or "document"
    sections = split_source_sections(
        source_text,
        max_chars=settings.section_max_chars,
        overlap_chars=0,
    )
    if not sections:
        raise ValueError("Nothing to translate.")
    _log(
        f"translate: {len(sections)} section(s) sequential, "
        f"lang={lang.value}, model={settings.chat_model}"
    )

    parts: list[str] = []
    prior_ending = ""
    system = (
        f"You rewrite documents into clear written {language_label(lang)}. "
        "Return only the document body."
    )
    for index, section in enumerate(sections):
        prompt = render_translate_prompt(
            section,
            title=display_title,
            part_index=index + 1,
            part_count=len(sections),
            prior_ending=prior_ending,
            language=lang,
        )
        with GatewayClient(settings) as gateway:
            part = gateway.chat_completion(
                model=settings.chat_model,
                user_prompt=prompt,
                system_prompt=system,
            )
        parts.append(part)
        prior_ending = last_sentences(part, count=2)
        _log(f"translate: completed {index + 1}/{len(sections)}")

    body = "\n\n".join(parts).strip()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    output_path = out or (
        settings.output_dir / f"{_slug(display_title)}-{lang.value}-{stamp}.md"
    )
    output_path.write_text(body + "\n", encoding="utf-8")
    _log(f"wrote {output_path}")
    return output_path


def _segment_path(work_dir: Path, index: int) -> Path:
    return work_dir / f"seg-{index:04d}.mp3"


def _synthesize_one(
    settings: Settings,
    index: int,
    text: str,
    work_dir: Path,
) -> tuple[int, Path]:
    path = _segment_path(work_dir, index)
    if path.exists() and path.stat().st_size > 0:
        return index, path
    # One client per worker: httpx.Client is not safe for concurrent use.
    with GatewayClient(settings) as gateway:
        audio = gateway.speech(
            model=settings.tts_model,
            text=text,
            voice=settings.tts_voice,
            speed=settings.tts_speed,
        )
    path.write_bytes(audio)
    return index, path


def run_pipeline(
    *,
    source_text: str,
    mode: Mode,
    settings: Settings,
    title: str | None = None,
    raw: bool = False,
    out: Path | None = None,
    language: Language | str | None = None,
    work_dir: Path | None = None,
) -> Path:
    """Rewrite (unless raw), chunk, parallel TTS with retries, stitch → Desktop MP3."""
    display_title = title or "document"
    lang = _parse_language(language if language is not None else settings.language)
    if raw:
        script = source_text.strip()
    else:
        script = _build_script(
            source_text=source_text,
            mode=mode,
            settings=settings,
            title=display_title,
            language=lang,
        )

    speak_chunks = chunk_script(script, max_words=settings.chunk_max_words)
    if not speak_chunks:
        raise ValueError("Nothing to speak after processing.")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    lang_tag = f"-{lang.value}" if lang != Language.en else ""
    output_path = out or (
        settings.output_dir
        / f"audiobook-{_slug(display_title)}-{mode.value}{lang_tag}-{stamp}.mp3"
    )
    segment_dir = work_dir or (
        settings.output_dir
        / f".audiobook-work-{_slug(display_title)}-{mode.value}{lang_tag}"
    )
    segment_dir.mkdir(parents=True, exist_ok=True)
    script_path = segment_dir / "script.txt"
    script_path.write_text(script + "\n", encoding="utf-8")
    _log(f"script: saved {script_path}")

    existing = sum(
        1
        for index in range(len(speak_chunks))
        if _segment_path(segment_dir, index).exists()
        and _segment_path(segment_dir, index).stat().st_size > 0
    )
    _log(
        f"tts: {len(speak_chunks)} chunk(s), {existing} cached, "
        f"concurrency={settings.tts_concurrency}, "
        f"speed={settings.tts_speed}, lang={lang.value}, work={segment_dir}"
    )

    workers = max(1, min(settings.tts_concurrency, len(speak_chunks)))
    by_index: dict[int, Path] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [
            pool.submit(_synthesize_one, settings, index, text, segment_dir)
            for index, text in enumerate(speak_chunks)
        ]
        done = 0
        for future in as_completed(futures):
            index, path = future.result()
            by_index[index] = path
            done += 1
            _log(f"tts: completed {done}/{len(speak_chunks)} (chunk {index + 1})")
    segment_paths = [by_index[i] for i in range(len(speak_chunks))]
    stitch_mp3_segments(segment_paths, output_path)
    _log(f"wrote {output_path}")
    return output_path

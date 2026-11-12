from __future__ import annotations

import re

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def chunk_script(script: str, max_words: int = 220) -> list[str]:
    """Split a spoken script into sentence-aware chunks for TTS."""
    cleaned = re.sub(r"\s+", " ", script).strip()
    if not cleaned:
        return []
    sentences = [s.strip() for s in _SENTENCE_SPLIT.split(cleaned) if s.strip()]
    if not sentences:
        return [cleaned]

    chunks: list[str] = []
    current: list[str] = []
    current_words = 0

    for sentence in sentences:
        words = len(sentence.split())
        if current and current_words + words > max_words:
            chunks.append(" ".join(current))
            current = [sentence]
            current_words = words
            continue
        current.append(sentence)
        current_words += words

    if current:
        chunks.append(" ".join(current))
    return chunks


def with_bridge_context(chunks: list[str]) -> list[str]:
    """Prepend a short bridge from the previous chunk so speech continues smoothly."""
    if len(chunks) <= 1:
        return chunks
    bridged: list[str] = [chunks[0]]
    for index, chunk in enumerate(chunks[1:], start=1):
        prev_tail = " ".join(chunks[index - 1].split()[-18:])
        bridged.append(
            f"(Continuing from: {prev_tail}) {chunk}"
        )
    return bridged

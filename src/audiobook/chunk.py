from __future__ import annotations

import re

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_NON_ALNUM = re.compile(r"[^a-z0-9\s]+")


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


def last_sentences(text: str, count: int = 2) -> str:
    """Return the last N sentences for continuity context (not spoken aloud)."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return ""
    sentences = [s.strip() for s in _SENTENCE_SPLIT.split(cleaned) if s.strip()]
    if not sentences:
        return cleaned
    return " ".join(sentences[-count:])


def _normalize_sentence(sentence: str) -> str:
    return _NON_ALNUM.sub("", sentence.lower()).strip()


def _token_set(sentence: str) -> set[str]:
    return {tok for tok in _normalize_sentence(sentence).split() if tok}


def _near_duplicate(a: str, b: str, *, jaccard_threshold: float = 0.82) -> bool:
    na = _normalize_sentence(a)
    nb = _normalize_sentence(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    if na.startswith(nb) or nb.startswith(na):
        shorter = min(len(na), len(nb))
        if shorter >= 40:
            return True
    ta = _token_set(a)
    tb = _token_set(b)
    if not ta or not tb:
        return False
    overlap = len(ta & tb) / len(ta | tb)
    return overlap >= jaccard_threshold


def dedupe_seam_sentences(script: str) -> str:
    """Drop a sentence that nearly repeats the previous one (section-join echoes)."""
    cleaned = re.sub(r"\s+", " ", script).strip()
    if not cleaned:
        return ""
    sentences = [s.strip() for s in _SENTENCE_SPLIT.split(cleaned) if s.strip()]
    if len(sentences) <= 1:
        return cleaned

    kept: list[str] = [sentences[0]]
    for sentence in sentences[1:]:
        if _near_duplicate(kept[-1], sentence):
            continue
        kept.append(sentence)
    return " ".join(kept)

from __future__ import annotations

import re


def split_source_sections(
    text: str,
    *,
    max_chars: int = 12000,
    overlap_chars: int = 0,
) -> list[str]:
    """Split long source into paragraph-bound sections.

    overlap_chars defaults to 0 so adjacent rewrites do not re-narrate the same
    source passage. Keep overlap at 0 unless you also pass prior-script context
    and seam dedupe.
    """
    cleaned = text.strip()
    if not cleaned:
        return []
    if len(cleaned) <= max_chars:
        return [cleaned]

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", cleaned) if p.strip()]
    if not paragraphs:
        paragraphs = [cleaned]

    sections: list[str] = []
    current: list[str] = []
    current_len = 0
    for para in paragraphs:
        para_len = len(para) + 2
        if current and current_len + para_len > max_chars:
            sections.append("\n\n".join(current))
            if overlap_chars > 0:
                overlap = sections[-1][-overlap_chars:]
                current = [overlap, para] if overlap else [para]
            else:
                current = [para]
            current_len = sum(len(p) + 2 for p in current)
            continue
        current.append(para)
        current_len += para_len
    if current:
        sections.append("\n\n".join(current))
    return sections

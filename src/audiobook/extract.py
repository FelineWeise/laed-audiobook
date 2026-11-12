from __future__ import annotations

from pathlib import Path


SUPPORTED_SUFFIXES = {".txt", ".md", ".markdown", ".html", ".htm", ".pdf"}


def extract_path(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"No such file: {path}")
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ValueError(
            f"Unsupported type {suffix!r}. Use one of: {sorted(SUPPORTED_SUFFIXES)}"
        )
    if suffix == ".pdf":
        return _extract_pdf(path)
    if suffix in {".html", ".htm"}:
        return _extract_html(path.read_text(encoding="utf-8", errors="replace"))
    if suffix in {".md", ".markdown"}:
        return _extract_markdown(path.read_text(encoding="utf-8", errors="replace"))
    return path.read_text(encoding="utf-8", errors="replace").strip()


def extract_clipboard(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Clipboard is empty.")
    return cleaned


def _extract_pdf(path: Path) -> str:
    import pymupdf

    doc = pymupdf.open(path)
    try:
        parts: list[str] = []
        for page in doc:
            parts.append(page.get_text("text"))
        return "\n\n".join(p.strip() for p in parts if p.strip()).strip()
    finally:
        doc.close()


def _extract_html(raw: str) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(raw, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text("\n")
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def _extract_markdown(raw: str) -> str:
    from markdown_it import MarkdownIt

    md = MarkdownIt()
    # Render to HTML then strip tags so we keep readable prose, not raw markup.
    return _extract_html(md.render(raw))

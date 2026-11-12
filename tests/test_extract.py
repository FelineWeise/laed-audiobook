from pathlib import Path

from audiobook.extract import extract_clipboard, extract_path


def test_extract_txt(tmp_path: Path) -> None:
    path = tmp_path / "note.txt"
    path.write_text("Hello audiobook.\n", encoding="utf-8")
    assert extract_path(path) == "Hello audiobook."


def test_extract_markdown(tmp_path: Path) -> None:
    path = tmp_path / "note.md"
    path.write_text("# Title\n\nA **bold** line.\n", encoding="utf-8")
    text = extract_path(path)
    assert "Title" in text
    assert "bold" in text
    assert "**" not in text


def test_extract_html(tmp_path: Path) -> None:
    path = tmp_path / "page.html"
    path.write_text("<html><body><p>Hi</p><script>x()</script></body></html>", encoding="utf-8")
    assert extract_path(path) == "Hi"


def test_clipboard_rejects_empty() -> None:
    try:
        extract_clipboard("   ")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_extract_pdf(tmp_path: Path) -> None:
    import pymupdf

    path = tmp_path / "page.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "PDF hello")
    doc.save(path)
    doc.close()
    assert "PDF hello" in extract_path(path)

from audiobook.section import split_source_sections


def test_short_text_single_section() -> None:
    assert split_source_sections("Hello world", max_chars=100) == ["Hello world"]


def test_long_text_splits_without_overlap_by_default() -> None:
    parts = [f"UniqueParagraph{i} content with enough characters to force splits. " + ("x" * 60) for i in range(20)]
    text = "\n\n".join(parts)
    sections = split_source_sections(text, max_chars=400)
    assert len(sections) > 1
    # Default overlap is 0: the closing unique marker of one section is absent from the next.
    for left, right in zip(sections, sections[1:]):
        left_marker = [line for line in left.splitlines() if line.startswith("UniqueParagraph")][-1]
        marker_id = left_marker.split()[0]
        assert marker_id not in right

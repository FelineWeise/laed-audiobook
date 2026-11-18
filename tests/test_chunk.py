from audiobook.chunk import chunk_script, dedupe_seam_sentences, last_sentences


def test_chunk_script_respects_word_budget() -> None:
    sentences = [f"Sentence number {i} with several extra words here." for i in range(40)]
    script = " ".join(sentences)
    chunks = chunk_script(script, max_words=40)
    assert len(chunks) > 1
    assert all(len(c.split()) <= 55 for c in chunks)


def test_last_sentences_returns_tail() -> None:
    text = "First sentence here. Second sentence follows. Third closes it."
    assert last_sentences(text, count=2) == "Second sentence follows. Third closes it."


def test_dedupe_seam_sentences_drops_near_repeat() -> None:
    script = (
        "Agents reshape how work gets done across the firm. "
        "Agents reshape how work gets done across the firm. "
        "Next we look at governance."
    )
    cleaned = dedupe_seam_sentences(script)
    assert cleaned.count("Agents reshape how work gets done across the firm.") == 1
    assert "Next we look at governance." in cleaned

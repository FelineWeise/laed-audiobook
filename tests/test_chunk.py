from audiobook.chunk import chunk_script, with_bridge_context


def test_chunk_script_respects_word_budget() -> None:
    sentences = [f"Sentence number {i} with several extra words here." for i in range(40)]
    script = " ".join(sentences)
    chunks = chunk_script(script, max_words=40)
    assert len(chunks) > 1
    assert all(len(c.split()) <= 55 for c in chunks)


def test_bridge_context_prefixes_continuation() -> None:
    chunks = [
        "Alpha beta gamma delta epsilon zeta eta theta.",
        "Next paragraph continues the story carefully.",
    ]
    bridged = with_bridge_context(chunks)
    assert bridged[0] == chunks[0]
    assert bridged[1].startswith("(Continuing from:")
    assert "Next paragraph" in bridged[1]

from audiobook.language import Language
from audiobook.modes import Mode, render_mode_prompt, render_translate_prompt


def test_render_includes_source() -> None:
    prompt = render_mode_prompt(Mode.review, "Source body here.", title="Brief")
    assert "Source body here." in prompt
    assert "Brief" in prompt
    assert "spoken" in prompt.lower() or "audio" in prompt.lower()
    assert "English" in prompt


def test_narrative_includes_paraphrase_guidance() -> None:
    prompt = render_mode_prompt(Mode.narrative, "Concept text.", title="Doc")
    assert "paraphrase" in prompt.lower()
    assert "In practice" in prompt or "Put another way" in prompt


def test_german_language_in_prompt() -> None:
    prompt = render_mode_prompt(
        Mode.narrative,
        "Concept text.",
        title="Doc",
        language=Language.de,
    )
    assert "German" in prompt
    assert "Praktisch heißt das" in prompt or "Anders gesagt" in prompt


def test_translate_prompt_is_written_german() -> None:
    prompt = render_translate_prompt("Hello world.", title="Doc", language=Language.de)
    assert "German" in prompt
    assert "written" in prompt.lower()
    assert "Hello world." in prompt


def test_continuation_context_in_prompt() -> None:
    prompt = render_mode_prompt(
        Mode.narrative,
        "New material.",
        title="Doc",
        part_index=2,
        part_count=3,
        prior_ending="We closed the last point about agents.",
    )
    assert "part 2 of 3" in prompt
    assert "We closed the last point about agents." in prompt
    assert "Do not restate" in prompt

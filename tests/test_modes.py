from audiobook.modes import Mode, render_mode_prompt


def test_render_includes_source() -> None:
    prompt = render_mode_prompt(Mode.review, "Source body here.", title="Brief")
    assert "Source body here." in prompt
    assert "Brief" in prompt
    assert "spoken" in prompt.lower() or "audio" in prompt.lower()

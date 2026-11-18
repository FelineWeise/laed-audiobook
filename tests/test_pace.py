from audiobook.pace import Pace, speed_for_pace


def test_pace_speed_presets() -> None:
    assert speed_for_pace(Pace.slow) == 0.85
    assert speed_for_pace(Pace.normal) == 1.0
    assert speed_for_pace(Pace.fast) == 1.15

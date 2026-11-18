from __future__ import annotations

from enum import Enum


class Pace(str, Enum):
    slow = "slow"
    normal = "normal"
    fast = "fast"


PACE_SPEED: dict[Pace, float] = {
    Pace.slow: 0.85,
    Pace.normal: 1.0,
    Pace.fast: 1.15,
}


def speed_for_pace(pace: Pace) -> float:
    return PACE_SPEED[pace]

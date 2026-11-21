"""Map candidate experience to difficulty bands."""

from __future__ import annotations

from src.taxonomy import EXPERIENCE_BANDS


def experience_options() -> list[str]:
    return list(EXPERIENCE_BANDS.keys())


def difficulties_for_experience(band: str) -> tuple[str, ...]:
    meta = EXPERIENCE_BANDS.get(band)
    if not meta:
        return ("beginner", "intermediate", "advanced", "senior", "expert")
    return meta["difficulties"]


def year_range_for_experience(band: str) -> tuple[int, int]:
    meta = EXPERIENCE_BANDS.get(band, {"years_min": 0, "years_max": 20})
    return int(meta["years_min"]), int(meta["years_max"])


def default_sort_key(difficulty: str) -> int:
    order = {"beginner": 0, "intermediate": 1, "advanced": 2, "senior": 3, "expert": 4}
    return order.get(difficulty, 99)

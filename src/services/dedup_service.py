"""Duplicate detection via normalized hash and Jaccard similarity."""

from __future__ import annotations

import hashlib
import re


_TOKEN_RE = re.compile(r"[a-z0-9]+")


def normalize_text(text: str) -> str:
    tokens = _TOKEN_RE.findall(text.lower())
    return " ".join(tokens)


def content_hash(title: str, stem: str) -> str:
    payload = normalize_text(f"{title} {stem}")
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def token_set(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def jaccard(a: str, b: str) -> float:
    sa, sb = token_set(a), token_set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def is_duplicate(
    title: str,
    stem: str,
    existing: list[tuple[str, str, str]],
    threshold: float = 0.85,
) -> tuple[bool, float, str | None]:
    """Return (is_dup, best_score, matching_id). existing tuples: id, title, stem."""
    candidate = f"{title} {stem}"
    cand_hash = content_hash(title, stem)
    best = 0.0
    match_id: str | None = None
    for sid, etitle, estem in existing:
        if content_hash(etitle, estem) == cand_hash:
            return True, 1.0, sid
        score = jaccard(candidate, f"{etitle} {estem}")
        if score > best:
            best = score
            match_id = sid
    if best >= threshold:
        return True, best, match_id
    return False, best, None

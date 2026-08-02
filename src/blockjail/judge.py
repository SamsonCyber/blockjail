"""Core jailbreak gate."""

from __future__ import annotations

from dataclasses import dataclass, field

from blockjail.normalize import decoded_variants, variants
from blockjail.patterns import BLOCK_CATEGORIES, COMPILED


@dataclass(frozen=True)
class Match:
    category: str
    evidence: str
    via: str  # which variant / decode method


@dataclass(frozen=True)
class Verdict:
    blocked: bool
    categories: tuple[str, ...] = ()
    matches: tuple[Match, ...] = field(default_factory=tuple)
    text_preview: str = ""

    def __bool__(self) -> bool:
        """True when blocked (so `if check(msg):` works as a gate)."""
        return self.blocked


def _scan_string(text: str, via: str) -> list[Match]:
    hits: list[Match] = []
    seen: set[str] = set()
    for variant in variants(text):
        for pattern, category in COMPILED:
            if category not in BLOCK_CATEGORIES:
                continue
            m = pattern.search(variant)
            if not m:
                continue
            if category in seen:
                continue
            seen.add(category)
            label = via if variant == text else f"{via}+norm"
            hits.append(
                Match(
                    category=category,
                    evidence=m.group(0)[:160],
                    via=label,
                )
            )
    return hits


def check(text: str, *, max_decode: int = 12) -> Verdict:
    """Inspect user text. Returns Verdict(blocked=True) if jailbreak-like.

    No network. No model. Pure local rules + light decode.
    """
    if not text or not str(text).strip():
        return Verdict(blocked=False, text_preview="")

    raw = str(text)
    matches: list[Match] = []
    seen_cat: set[str] = set()

    def absorb(more: list[Match]) -> None:
        for m in more:
            if m.category not in seen_cat:
                seen_cat.add(m.category)
                matches.append(m)

    absorb(_scan_string(raw, "raw"))

    for method, decoded in decoded_variants(raw)[:max_decode]:
        absorb(_scan_string(decoded, method))

    cats = tuple(sorted(seen_cat))
    return Verdict(
        blocked=bool(matches),
        categories=cats,
        matches=tuple(matches),
        text_preview=raw[:200],
    )


def is_blocked(text: str) -> bool:
    """Convenience: True if the text should be blocked."""
    return check(text).blocked

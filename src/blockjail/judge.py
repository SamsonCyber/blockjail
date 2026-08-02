"""Core jailbreak gate."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from blockjail.normalize import decoded_variants, variants
from blockjail.patterns import BLOCK_CATEGORIES, COMPILED

_ZW = frozenset("\u200b\u200c\u200d\ufeff\u2060")


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


def _channel_hits(text: str) -> list[Match]:
    """Light stego-ish channel signals (indent / NBSP / zero-width)."""
    hits: list[Match] = []

    # Indent bit-channel: both 2-space and 4-space indents with enough bits
    two = four = 0
    for line in text.split("\n"):
        if not line.strip():
            continue
        m = re.match(r"^( +)", line)
        if not m or "\t" in m.group(1):
            continue
        n = len(m.group(1))
        if n == 2:
            two += 1
        elif n == 4:
            four += 1
    if two >= 4 and four >= 4 and (two + four) >= 16:
        hits.append(
            Match(
                category="indent_channel",
                evidence=f"two_space={two} four_space={four}",
                via="channel",
            )
        )

    # Space vs NBSP between words
    parts = re.split(r"([ \u00a0]+)", text)
    nbsp_runs = space_runs = 0
    for p in parts:
        if not p:
            continue
        if set(p) <= {"\u00a0"}:
            nbsp_runs += 1
        elif set(p) <= {" "}:
            space_runs += 1
    if nbsp_runs >= 3 and space_runs >= 3 and (nbsp_runs + space_runs) >= 8:
        hits.append(
            Match(
                category="nbsp_channel",
                evidence=f"nbsp_runs={nbsp_runs} space_runs={space_runs}",
                via="channel",
            )
        )

    # Sparse zero-width (any multi-type or count>=2 is a tripwire for solo apps)
    zw_count = sum(1 for ch in text if ch in _ZW)
    types = {ch for ch in text if ch in _ZW}
    if zw_count >= 2 or len(types) >= 2:
        hits.append(
            Match(
                category="zero_width",
                evidence=f"count={zw_count} types={len(types)}",
                via="channel",
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
    absorb(_channel_hits(raw))

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


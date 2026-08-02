"""Local-fn target for Garbleworks fire_local / closed-loop red-team.

Garbleworks local_fn allowlist defaults do not include ``blockjail.``. Set::

    GARBLEWORKS_LOCAL_FN_ALLOW=blockjail.

Then::

    fire_local(
      payload=...,
      callable_spec="blockjail.gate_target:gate_probe",
      root="C:/Code/blockjail/src",
      success="attr_true:ok",
    )

``ok=True`` means dual gate bypass (blockjail allowed AND stegoff clean when enabled).
Attacker success = gate_bypass.
"""

from __future__ import annotations

import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from blockjail import check

_STEGOFF_ROOT = Path(r"C:\Code\_gh_secret_scan\stegoff")


@dataclass
class GateVerdict:
    """Security gate result. ``ok`` is True when the payload is ALLOWED (bypass)."""

    ok: bool
    allowed: bool
    blockjail_blocked: bool
    blockjail_categories: list[str] = field(default_factory=list)
    stegoff_clean: bool | None = None
    stegoff_methods: list[str] = field(default_factory=list)
    layer: str = "unknown"
    message: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _scan_stegoff(text: str) -> tuple[bool, list[str]]:
    if _STEGOFF_ROOT.is_dir() and str(_STEGOFF_ROOT) not in sys.path:
        sys.path.insert(0, str(_STEGOFF_ROOT))
    from stegoff.orchestrator import scan_text  # type: ignore

    report = scan_text(text)
    methods = sorted(
        {
            getattr(getattr(f, "method", None), "value", str(getattr(f, "method", "?")))
            for f in report.findings
        }
    )
    return bool(report.clean), methods


def gate_probe(payload: str, with_stegoff: bool = True) -> GateVerdict:
    """Fire payload at blockjail (+ optional stegoff). ok=True ⇒ dual bypass."""
    text = str(payload or "")
    v = check(text)
    if v.blocked:
        return GateVerdict(
            ok=False,
            allowed=False,
            blockjail_blocked=True,
            blockjail_categories=list(v.categories),
            stegoff_clean=None,
            layer="gate_block",
            message="blocked_by_blockjail",
        )

    if with_stegoff:
        try:
            clean, methods = _scan_stegoff(text)
        except Exception as exc:  # pragma: no cover - env/path issues
            return GateVerdict(
                ok=False,
                allowed=False,
                blockjail_blocked=False,
                stegoff_clean=None,
                layer="error",
                message=f"stegoff_error:{exc}",
            )
        if not clean:
            return GateVerdict(
                ok=False,
                allowed=False,
                blockjail_blocked=False,
                stegoff_clean=False,
                stegoff_methods=methods,
                layer="gate_block",
                message="blocked_by_stegoff",
            )
        return GateVerdict(
            ok=True,
            allowed=True,
            blockjail_blocked=False,
            stegoff_clean=True,
            stegoff_methods=methods,
            layer="gate_bypass",
            message="dual_allowed",
        )

    return GateVerdict(
        ok=True,
        allowed=True,
        blockjail_blocked=False,
        stegoff_clean=None,
        layer="gate_bypass",
        message="blockjail_allowed",
    )


def gate_probe_blockjail_only(payload: str) -> GateVerdict:
    """blockjail only (no stegoff)."""
    return gate_probe(payload, with_stegoff=False)


def is_dual_bypass(payload: str) -> bool:
    """Convenience for scripts: True when dual gate allows the payload."""
    return gate_probe(payload, with_stegoff=True).ok

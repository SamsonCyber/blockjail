"""
Tiny solo app: chat endpoint gated by blockjail (+ optional stegoff scan_text).

Usage:
  py -3.12 examples/gated_app.py
  py -3.12 examples/gated_app.py --with-stegoff

This is a demo harness for red-team probes, not a production server.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

# ensure src on path when run from repo
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from blockjail import check  # noqa: E402


@dataclass
class GateResult:
    allowed: bool
    message: str
    blockjail_blocked: bool
    blockjail_categories: list[str] = field(default_factory=list)
    stegoff_clean: bool | None = None
    stegoff_methods: list[str] = field(default_factory=list)
    assistant: str = ""


class TinyGatedApp:
    """Minimal chat app with local gates."""

    def __init__(self, with_stegoff: bool = False) -> None:
        self.with_stegoff = with_stegoff
        self._scan_text = None
        if with_stegoff:
            stegoff_root = Path(r"C:\Code\_gh_secret_scan\stegoff")
            if stegoff_root.is_dir():
                sys.path.insert(0, str(stegoff_root))
            from stegoff.orchestrator import scan_text  # type: ignore

            self._scan_text = scan_text

    def handle(self, user_message: str) -> GateResult:
        # Layer 1: blockjail (always)
        v = check(user_message)
        if v.blocked:
            return GateResult(
                allowed=False,
                message="blocked_by_blockjail",
                blockjail_blocked=True,
                blockjail_categories=list(v.categories),
                stegoff_clean=None,
            )

        # Layer 2: optional stegoff text scan
        stegoff_clean: bool | None = None
        methods: list[str] = []
        if self._scan_text is not None:
            report = self._scan_text(user_message)
            stegoff_clean = bool(report.clean)
            methods = sorted(
                {
                    getattr(getattr(f, "method", None), "value", str(getattr(f, "method", "?")))
                    for f in report.findings
                }
            )
            if not report.clean:
                return GateResult(
                    allowed=False,
                    message="blocked_by_stegoff",
                    blockjail_blocked=False,
                    stegoff_clean=False,
                    stegoff_methods=methods,
                )

        # "Model" — dummy echo so we only measure the gate
        return GateResult(
            allowed=True,
            message="allowed",
            blockjail_blocked=False,
            stegoff_clean=stegoff_clean,
            stegoff_methods=methods,
            assistant=f"OK: processed {len(user_message)} chars",
        )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--with-stegoff", action="store_true")
    p.add_argument("--json-line", action="store_true", help="Read one JSON {message} from stdin")
    p.add_argument("message", nargs="?", help="Single message to gate")
    args = p.parse_args(argv)

    app = TinyGatedApp(with_stegoff=args.with_stegoff)
    if args.message is not None:
        msg = args.message
    elif args.json_line:
        msg = json.loads(sys.stdin.read()).get("message", "")
    else:
        msg = sys.stdin.read()

    result = app.handle(msg)
    print(json.dumps(asdict(result), indent=2))
    return 0 if result.allowed else 2


if __name__ == "__main__":
    raise SystemExit(main())

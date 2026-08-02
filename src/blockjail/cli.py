"""CLI: blockjail "text" | blockjail --json"""

from __future__ import annotations

import argparse
import json
import sys

from blockjail.judge import check


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="blockjail",
        description="Tiny local jailbreak gate. Exit 0=allow, 2=block.",
    )
    p.add_argument("text", nargs="?", help="Text to check (or read stdin)")
    p.add_argument("--json", action="store_true", help="JSON verdict on stdout")
    p.add_argument("-q", "--quiet", action="store_true", help="No stdout; exit code only")
    args = p.parse_args(argv)

    if args.text is not None:
        text = args.text
    else:
        text = sys.stdin.read()

    v = check(text)
    if args.json:
        print(
            json.dumps(
                {
                    "blocked": v.blocked,
                    "categories": list(v.categories),
                    "matches": [
                        {"category": m.category, "evidence": m.evidence, "via": m.via}
                        for m in v.matches
                    ],
                },
                indent=2,
            )
        )
    elif not args.quiet:
        if v.blocked:
            print("BLOCK", ",".join(v.categories) or "jailbreak")
        else:
            print("ALLOW")

    return 2 if v.blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())

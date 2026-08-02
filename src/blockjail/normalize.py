"""Text normalization + light decode for tokenizer / encoding games."""

from __future__ import annotations

import base64
import codecs
import html
import re
from urllib.parse import unquote

_LEET_MAP = str.maketrans({
    "0": "o", "1": "i", "3": "e", "4": "a", "5": "s",
    "7": "t", "8": "b", "9": "g", "@": "a", "$": "s",
    "!": "i", "+": "t",
})


def leetspeak(text: str) -> str:
    return text.translate(_LEET_MAP)


def collapse_char_spaced(text: str) -> str:
    tokens = text.split()
    if len(tokens) < 8:
        return text
    single = sum(1 for t in tokens if len(t) == 1)
    if single / len(tokens) < 0.75:
        return text
    return "".join(tokens)


def token_boundaries(text: str) -> str:
    t = text.replace("_", " ").replace("\x00", " ")
    t = re.sub(r"(?<=[A-Za-z])\.(?=[A-Za-z])", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def variants(text: str) -> list[str]:
    """Unique scan variants (original + normalized)."""
    out: list[str] = []
    seen: set[str] = set()

    def add(v: str) -> None:
        if v and len(v) >= 5 and v not in seen:
            seen.add(v)
            out.append(v)

    add(text)
    add(leetspeak(text))
    add(token_boundaries(text))
    add(collapse_char_spaced(text))
    add(token_boundaries(collapse_char_spaced(text)))
    add(leetspeak(token_boundaries(text)))
    if "\x00" in text:
        add(text.replace("\x00", " "))
        add(text.replace("\x00", ""))
    # HTML entities
    unesc = html.unescape(text)
    if unesc != text:
        add(unesc)
    return out


def _looks_text(s: str) -> bool:
    if not s or len(s) < 6:
        return False
    sample = s[:400]
    printable = sum(1 for c in sample if c.isprintable() or c in "\n\r\t")
    return printable / max(len(sample), 1) >= 0.85


def decoded_variants(text: str) -> list[tuple[str, str]]:
    """Light multi-decode: rot13, hex, percent, base64, quoted-printable-ish.

    Returns list of (method, decoded). Only include plausible text.
    """
    found: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add(method: str, s: str) -> None:
        if s and s != text and s not in seen and _looks_text(s):
            seen.add(s)
            found.append((method, s))

    stripped = text.strip()

    # ROT13
    rot = codecs.decode(stripped, "rot_13")
    if rot != stripped:
        add("rot13", rot)

    # Percent
    if "%" in stripped:
        try:
            add("percent", unquote(stripped))
        except Exception:
            pass

    # Continuous hex
    compact = re.sub(r"\s+", "", stripped)
    if len(compact) >= 12 and len(compact) % 2 == 0 and re.fullmatch(r"[0-9a-fA-F]+", compact):
        try:
            add("hex", bytes.fromhex(compact).decode("utf-8"))
        except Exception:
            pass

    # Base64 tokens (+ rot13 of decoded, common double wrap)
    for m in re.findall(r"[A-Za-z0-9+/]{20,}={0,2}", text)[:8]:
        try:
            pad = "=" * ((4 - len(m) % 4) % 4)
            dec = base64.b64decode(m + pad).decode("utf-8")
            add("b64", dec)
            rot_dec = codecs.decode(dec, "rot_13")
            if rot_dec != dec:
                add("b64+rot13", rot_dec)
        except Exception:
            pass

    # Dense =XX quoted-printable
    if re.search(r"(?:=[0-9A-Fa-f]{2}){8,}", re.sub(r"\s+", "", text)):
        try:
            import quopri

            add(
                "qp",
                quopri.decodestring(text.encode("ascii", errors="ignore")).decode("utf-8"),
            )
        except Exception:
            try:
                raw = bytearray()
                s = re.sub(r"\s+", "", text)
                i = 0
                while i < len(s):
                    if s[i] == "=" and i + 2 < len(s):
                        raw.append(int(s[i + 1 : i + 3], 16))
                        i += 3
                    else:
                        raw.append(ord(s[i]))
                        i += 1
                add("qp", raw.decode("utf-8"))
            except Exception:
                pass

    return found

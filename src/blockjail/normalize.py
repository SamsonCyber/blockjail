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

# Common Cyrillic / Greek lookalikes → Latin (homoglyph soft frames)
_HOMOGLYPH_MAP = str.maketrans({
    "а": "a", "А": "A",  # Cyrillic a
    "е": "e", "Е": "E",
    "о": "o", "О": "O",
    "р": "p", "Р": "P",
    "с": "c", "С": "C",
    "у": "y", "У": "Y",
    "х": "x", "Х": "X",
    "і": "i", "І": "I",
    "κ": "k", "Κ": "K",  # Greek
    "ν": "v", "ο": "o", "Ο": "O",
    "ρ": "p", "с": "c",
})


def leetspeak(text: str) -> str:
    return text.translate(_LEET_MAP)


def dehomoglyph(text: str) -> str:
    return text.translate(_HOMOGLYPH_MAP)


def _caesar(text: str, shift: int) -> str:
    out: list[str] = []
    for c in text:
        if "a" <= c <= "z":
            out.append(chr((ord(c) - 97 + shift) % 26 + 97))
        elif "A" <= c <= "Z":
            out.append(chr((ord(c) - 65 + shift) % 26 + 65))
        else:
            out.append(c)
    return "".join(out)


def atbash(text: str) -> str:
    out: list[str] = []
    for c in text:
        if "a" <= c <= "z":
            out.append(chr(97 + 25 - (ord(c) - 97)))
        elif "A" <= c <= "Z":
            out.append(chr(65 + 25 - (ord(c) - 65)))
        else:
            out.append(c)
    return "".join(out)


def defullwidth(text: str) -> str:
    out: list[str] = []
    for c in text:
        o = ord(c)
        if 0xFF01 <= o <= 0xFF5E:
            out.append(chr(o - 0xFEE0))
        elif c == "\u3000":
            out.append(" ")
        else:
            out.append(c)
    return "".join(out)


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
    add(dehomoglyph(text))
    add(leetspeak(dehomoglyph(text)))
    add(defullwidth(text))
    add(dehomoglyph(defullwidth(text)))
    add(token_boundaries(text))
    add(collapse_char_spaced(text))
    add(token_boundaries(collapse_char_spaced(text)))
    add(leetspeak(token_boundaries(text)))
    add(dehomoglyph(token_boundaries(text)))
    # Reversed full string / reversed tokens (evasion)
    if len(text) >= 12:
        add(text[::-1])
        words = text.split()
        if len(words) >= 4:
            add(" ".join(w[::-1] for w in words))
            add(" ".join(reversed(words)))
    # Caesar shifts 1-12 and atbash (injection-gated by pattern scan)
    if 12 <= len(text) <= 4000:
        add(atbash(text))
        for k in range(1, 13):
            add(_caesar(text, k))
    # Quoted-string join (pack-hunt / list-smuggle)
    quoted = re.findall(r'"([^"\n]{2,80})"', text)
    if len(quoted) >= 4:
        add(" ".join(quoted))
    quoted_s = re.findall(r"'([^'\n]{2,80})'", text)
    if len(quoted_s) >= 4:
        add(" ".join(quoted_s))
    if "\x00" in text:
        add(text.replace("\x00", " "))
        add(text.replace("\x00", ""))
    # HTML entities
    unesc = html.unescape(text)
    if unesc != text:
        add(unesc)
        add(dehomoglyph(unesc))
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

    def try_b64(blob: str, label: str) -> None:
        for m in re.findall(r"[A-Za-z0-9+/]{20,}={0,2}", blob)[:8]:
            try:
                pad = "=" * ((4 - len(m) % 4) % 4)
                dec = base64.b64decode(m + pad).decode("utf-8")
                add(label, dec)
                rot_dec = codecs.decode(dec, "rot_13")
                if rot_dec != dec:
                    add(f"{label}+rot13", rot_dec)
            except Exception:
                pass
        # whole-string base64
        if re.fullmatch(r"[A-Za-z0-9+/]{20,}={0,2}", blob):
            try:
                pad = "=" * ((4 - len(blob) % 4) % 4)
                add(label, base64.b64decode(blob + pad).decode("utf-8"))
            except Exception:
                pass

    # ROT13
    rot = codecs.decode(stripped, "rot_13")
    if rot != stripped:
        add("rot13", rot)

    # Percent (+ chain into base64)
    if "%" in stripped:
        try:
            pct = unquote(stripped)
            add("percent", pct)
            try_b64(pct, "percent+b64")
        except Exception:
            pass

    # Continuous hex
    compact = re.sub(r"\s+", "", stripped)
    if len(compact) >= 12 and len(compact) % 2 == 0 and re.fullmatch(r"[0-9a-fA-F]+", compact):
        try:
            add("hex", bytes.fromhex(compact).decode("utf-8"))
        except Exception:
            pass

    # Base64 tokens (+ rot13 / caesar of decoded)
    try_b64(text, "b64")
    for m in re.findall(r"[A-Za-z0-9+/]{20,}={0,2}", text)[:6]:
        try:
            pad = "=" * ((4 - len(m) % 4) % 4)
            dec = base64.b64decode(m + pad).decode("utf-8")
            if 12 <= len(dec) <= 2000:
                add("b64+atbash", atbash(dec))
                for k in (1, 2, 3, 5, 7, 13):
                    add(f"b64+caesar{k}", _caesar(dec, k))
        except Exception:
            pass

    # ascii85 / base85 whole-string (injection-gated via pattern scan)
    if len(stripped) >= 20:
        for label, fn in (("a85", base64.a85decode), ("b85", base64.b85decode)):
            try:
                add(label, fn(stripped.encode("ascii", errors="ignore")).decode("utf-8"))
            except Exception:
                pass

    # zlib-wrapped base64
    for m in re.findall(r"[A-Za-z0-9+/]{20,}={0,2}", text)[:4]:
        try:
            import zlib

            pad = "=" * ((4 - len(m) % 4) % 4)
            raw = base64.b64decode(m + pad)
            add("zlib+b64", zlib.decompress(raw).decode("utf-8"))
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

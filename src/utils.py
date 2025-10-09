from __future__ import annotations
import hashlib, re, unicodedata
import orjson
from typing import Any, Tuple

WHITESPACE_RE = re.compile(r"\s+", re.MULTILINE)
ZERO_WIDTH_RE = re.compile(r"[\u200B-\u200D\uFEFF]")

def normalize_text(text: str) -> str:
    t = unicodedata.normalize("NFKC", text).replace("\r\n","\n").replace("\r","\n")
    t = ZERO_WIDTH_RE.sub("", t)
    t = WHITESPACE_RE.sub(" ", t).strip()
    return t

def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def _extract_json_balanced(s: str) -> str | None:
    # Extract the first balanced JSON object, respecting quotes/escapes
    start = s.find("{")
    if start == -1:
        return None
    in_str = False
    esc = False
    depth = 0
    for i in range(start, len(s)):
        ch = s[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return s[start:i+1]
    return None

def extract_first_json_candidate(s: str) -> str | None:
    return _extract_json_balanced(s)

def parse_envelope(text: str) -> Tuple[dict[str, Any] | None, str | None]:
    try:
        return orjson.loads(text), None
    except Exception as e1:
        candidate = extract_first_json_candidate(text)
        if candidate:
            try:
                return orjson.loads(candidate), None
            except Exception as e2:
                return None, f"JSON extract failed: {e2}"
        return None, "No JSON found"

from __future__ import annotations
import hashlib, re
import orjson
from typing import Any, Tuple

WHITESPACE_RE = re.compile(r"\s+", re.MULTILINE)
JSON_CANDIDATE_RE = re.compile(r"\{[\s\S]*\}")

def normalize_text(text: str) -> str:
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    t = WHITESPACE_RE.sub(" ", t).strip()
    return t

def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def extract_first_json_candidate(s: str) -> str | None:
    m = JSON_CANDIDATE_RE.search(s)
    return m.group(0) if m else None

def parse_envelope(text: str) -> Tuple[dict[str, Any] | None, str | None]:
    try:
        return orjson.loads(text), None
    except Exception:
        candidate = extract_first_json_candidate(text)
        if candidate:
            try:
                return orjson.loads(candidate), None
            except Exception as e2:
                return None, f"JSON extract failed: {e2}"
        return None, "No JSON found"

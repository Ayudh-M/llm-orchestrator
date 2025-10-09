
from __future__ import annotations
import json, unicodedata, hashlib
from typing import Any, Dict
from .schemas import Envelope

def normalize_text(s: str) -> str:
    # NFKC and remove ZERO WIDTH space
    s = unicodedata.normalize("NFKC", s)
    return s.replace("\u200B", "")

def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def parse_envelope(s: str) -> Envelope:
    data = json.loads(s)
    return Envelope.model_validate(data)

def to_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=False)

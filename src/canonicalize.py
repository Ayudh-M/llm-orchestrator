
from __future__ import annotations
import json, re

def _collapse_ws(s: str) -> str:
    return " ".join(s.strip().split())

def canonicalize_for_hash(text: str) -> str:
    # Try JSON minify & sort
    t = text.strip()
    try:
        obj = json.loads(t)
        return json.dumps(obj, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
    except Exception:
        pass

    # Try heuristic SQL normalization: strip comments and collapse WS
    # Remove /* */ and -- comments (but keep quoted strings intact)
    s = t
    # remove /* ... */ blocks
    s = re.sub(r"/\*.*?\*/", " ", s, flags=re.DOTALL)
    # remove -- to end-of-line
    s = re.sub(r"--.*?$", " ", s, flags=re.MULTILINE)
    s = _collapse_ws(s)
    return s

from __future__ import annotations
import json, re, decimal

_SQL_COMMENT_LINE = re.compile(r"--.*?$", flags=re.MULTILINE)
_SQL_COMMENT_BLOCK = re.compile(r"/\*.*?\*/", flags=re.DOTALL)
_WS = re.compile(r"\s+")

def _is_json_like(s: str) -> bool:
    s = s.strip()
    return (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]"))

def _is_sql_like(s: str) -> bool:
    return bool(re.match(r"^(WITH|SELECT|INSERT|UPDATE|DELETE)\b", s.strip(), flags=re.IGNORECASE))

def _is_number_like(s: str) -> bool:
    try:
        decimal.Decimal(s.strip())
        return True
    except Exception:
        return False

def _minify_json(s: str) -> str:
    try:
        obj = json.loads(s)
        return json.dumps(obj, separators=(',', ':'), sort_keys=True, ensure_ascii=False)
    except Exception:
        return s.strip()

def _normalize_sql(s: str) -> str:
    s0 = _SQL_COMMENT_BLOCK.sub(" ", s)
    s0 = _SQL_COMMENT_LINE.sub(" ", s0)
    # collapse whitespace outside quotes (simple heuristic)
    out, in_str, quote = [], False, ''
    for ch in s0:
        if ch in ('"', "'"):
            if not in_str:
                in_str, quote = True, ch
            elif quote == ch:
                in_str, quote = False, ''
            out.append(ch)
            continue
        if in_str:
            out.append(ch)
        else:
            out.append(ch if not ch.isspace() else ' ')
    # collapse spaces and trim
    return _WS.sub(" ", ''.join(out)).strip()

def _normalize_number(s: str) -> str:
    d = decimal.Decimal(s.strip())
    # remove trailing zeros where possible
    normalized = format(d.normalize(), 'f').rstrip('0').rstrip('.')
    return normalized if normalized else "0"

def canonicalize_for_hash(text: str) -> str:
    if text is None:
        return ""
    s = text.strip()
    if _is_json_like(s):
        return _minify_json(s)
    if _is_sql_like(s):
        return _normalize_sql(s)
    if _is_number_like(s):
        return _normalize_number(s)
    # default: collapse whitespace
    return re.sub(r"\s+", " ", s).strip()

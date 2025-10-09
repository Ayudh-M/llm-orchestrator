from __future__ import annotations
import json, os
from typing import Any, Tuple, List

try:
    import jsonschema
    _HAS_JSONSCHEMA = True
except Exception:
    _HAS_JSONSCHEMA = False

_SCHEMA_CACHE: dict[str, Any] = {}

def _load_schema(path: str) -> Any:
    if path in _SCHEMA_CACHE:
        return _SCHEMA_CACHE[path]
    with open(path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    _SCHEMA_CACHE[path] = schema
    return schema

def validate_envelope(obj: dict, schema_path: str) -> Tuple[bool, List[str]]:
    if not _HAS_JSONSCHEMA:
        return True, []
    schema = _load_schema(schema_path)
    v = jsonschema.Draft2020Validator(schema)
    errors = sorted(v.iter_errors(obj), key=lambda e: e.path)
    msgs = [f"{'/'.join(map(str,e.path))}: {e.message}" if e.path else e.message for e in errors]
    return (len(msgs) == 0), msgs

def coerce_minimal_defaults(obj: dict) -> dict:
    # Add minimal defaults for required fields if missing
    obj.setdefault("role", obj.get("role",""))
    obj.setdefault("domain", obj.get("domain",""))
    obj.setdefault("task_understanding", obj.get("task_understanding",""))
    obj.setdefault("public_message", obj.get("public_message",""))
    obj.setdefault("artifact", obj.get("artifact", {"type":"results","content":{}}))
    obj.setdefault("needs_from_peer", obj.get("needs_from_peer", []))
    obj.setdefault("handoff_to", obj.get("handoff_to", ""))
    obj.setdefault("status", obj.get("status", "WORKING"))
    obj.setdefault("final_solution", obj.get("final_solution", {"canonical_text":"","sha256":""}))
    obj.setdefault("tags", obj.get("tags", []))
    obj.setdefault("request", obj.get("request", {"to_peer": None}))
    obj.setdefault("meta", obj.get("meta", {}))
    obj.setdefault("scratch", obj.get("scratch", {}))
    return obj

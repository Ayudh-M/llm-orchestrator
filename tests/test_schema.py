import os, json
from src.json_enforcer import validate_envelope, coerce_minimal_defaults

SCHEMA = os.path.join(os.path.dirname(os.path.dirname(__file__)), "schemas", "envelope.schema.json")

def test_schema_validate_and_coerce():
    obj = {"role":"R","domain":"D","status":"SOLVED","final_solution":{"canonical_text":"X","sha256":""},
           "artifact":{"type":"results","content":{}}, "needs_from_peer":[], "handoff_to":"peer",
           "task_understanding":"", "public_message":"[SOLVED]"}
    ok, errs = validate_envelope(obj, SCHEMA)
    assert ok, f"should be valid: {errs}"
    # drop a required field, it should be caught
    bad = obj.copy(); bad.pop("artifact")
    ok2, errs2 = validate_envelope(bad, SCHEMA)
    assert not ok2 and errs2
    fixed = coerce_minimal_defaults(bad)
    ok3, errs3 = validate_envelope(fixed, SCHEMA)
    assert ok3, f"coerced should validate: {errs3}"

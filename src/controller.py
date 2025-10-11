from __future__ import annotations
from typing import Dict, Any, Tuple, Optional, List
from pydantic import ValidationError
from .schemas import Envelope
from .canonicalize import canonicalize_for_hash
from .utils import to_json, sha256_hex
from .sanitize import repair_envelope

def _checked(env_dict: Dict[str, Any]) -> Envelope:
    try:
        return Envelope.model_validate(env_dict)
    except ValidationError:
        repaired = repair_envelope(env_dict)
        return Envelope.model_validate(repaired)


def _canon_and_hash(s: str, kind: Optional[str] = None) -> Tuple[str, str]:
    canon = canonicalize_for_hash(s, kind=kind)
    return canon, sha256_hex(canon)

def run_controller(task: str, agent_a, agent_b, max_rounds: int = 8, kind: Optional[str] = None):
    transcript: List[Dict[str, Any]] = []
    final_a = final_b = None
    for r in range(1, max_rounds + 1):
        env_a_raw, raw_a = agent_a.step(task, transcript)
        env_b_raw, raw_b = agent_b.step(task, transcript)

        env_a = _checked(env_a_raw)
        env_b = _checked(env_b_raw)

        rec = {"round": r, "a":{"envelope": env_a_raw, "raw": raw_a}, "b":{"envelope": env_b_raw, "raw": raw_b}}
        transcript.append(rec)

        if env_a.is_solved(): final_a = env_a.final_solution.canonical_text
        if env_b.is_solved(): final_b = env_b.final_solution.canonical_text

        if final_a and final_b:
            ca, ha = _canon_and_hash(final_a, kind)
            cb, hb = _canon_and_hash(final_b, kind)
            if ca == cb:
                return {
                    "status": "CONSENSUS",
                    "rounds": r,
                    "canonical_text": ca,
                    "sha256": ha,
                    "transcript": transcript
                }
    return {"status":"NO_CONSENSUS", "rounds": max_rounds, "transcript": transcript}

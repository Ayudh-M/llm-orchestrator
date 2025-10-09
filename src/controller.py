
from __future__ import annotations
from typing import Dict, Any, Tuple, Optional, List
import time, json
from .schemas import Envelope, Status
from .canonicalize import canonicalize_for_hash
from .utils import to_json, sha256_hex

def _checked(env_dict: Dict[str, Any]) -> Envelope:
    return Envelope.model_validate(env_dict)

def _canon_and_hash(s: str) -> Tuple[str, str]:
    canon = canonicalize_for_hash(s)
    return canon, sha256_hex(canon)

def _verify_solution(env: Envelope) -> Tuple[bool, str]:
    if not env.is_solved():
        return False, "not solved or missing final_solution"
    if not env.final_solution.canonical_text.strip():
        return False, "empty canonical_text"
    return True, "ok"

def run_controller(task: str, agent_a, agent_b, max_rounds: int = 12, task_type: str = "generic") -> Dict[str, Any]:
    """agent.step(task, transcript) -> (env_dict, raw_text)"""
    transcript: List[Dict[str, Any]] = []
    last_from_b: Optional[Envelope] = None

    for r in range(1, max_rounds+1):
        # A step
        env_a_dict, raw_a = agent_a.step(task, transcript)
        env_a = _checked(env_a_dict)
        transcript.append({"t": r, "actor": "A", "envelope": env_a.model_dump(), "raw": raw_a})

        # B step (peer sees A envelope)
        env_b_dict, raw_b = agent_b.step(task, transcript)
        env_b = _checked(env_b_dict)
        transcript.append({"t": r, "actor": "B", "envelope": env_b.model_dump(), "raw": raw_b})

        # If both SOLVED, check consensus
        if env_a.status == Status.SOLVED and env_b.status == Status.SOLVED:
            ok_a, _ = _verify_solution(env_a)
            ok_b, _ = _verify_solution(env_b)
            if not (ok_a and ok_b):
                continue
            a_norm, a_hash = _canon_and_hash(env_a.final_solution.canonical_text)
            b_norm, b_hash = _canon_and_hash(env_b.final_solution.canonical_text)
            # backfill hashes if missing
            if env_a.final_solution.sha256 is None:
                env_a_dict["final_solution"]["sha256"] = a_hash
            if env_b.final_solution.sha256 is None:
                env_b_dict["final_solution"]["sha256"] = b_hash

            if a_norm == b_norm and a_hash == b_hash:
                return {
                    "status": "CONSENSUS",
                    "canonical_text": a_norm,
                    "sha256": a_hash,
                    "rounds": r,
                    "transcript": transcript,
                    "final_a": env_a_dict,
                    "final_b": env_b_dict,
                }
            else:
                # disagreement; continue if rounds left
                pass

    return {
        "status": "NO_CONSENSUS",
        "reason": "max_rounds_exceeded_or_mismatch",
        "rounds": max_rounds,
        "transcript": transcript,
    }

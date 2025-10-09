from __future__ import annotations
from typing import Dict, Any, List, Tuple
from .schemas import Envelope
from .utils import normalize_text, sha256_hex

def _checked(env_dict: Dict[str, Any]) -> Envelope:
    return Envelope.model_validate(env_dict)

def _verify_solution(env: Envelope) -> Tuple[bool, str]:
    if not env.is_solved():
        return False, "not solved or missing [SOLVED] or canonical_text"
    return True, "ok"

def run_controller(task: str, agent_a, agent_b, max_rounds: int = 8) -> Dict[str, Any]:
    transcript: List[Dict[str, Any]] = []
    mismatch_count = 0
    for r in range(1, max_rounds+1):
        # Agent A
        a_obj, a_raw = agent_a.step(task, transcript)
        a_env = _checked(a_obj)
        a_norm = normalize_text(a_env.final_solution.canonical_text or "")
        a_env.final_solution.sha256 = sha256_hex(a_norm) if a_norm else ""
        transcript.append(a_env.model_dump())

        # Agent B
        b_obj, b_raw = agent_b.step(task, transcript)
        b_env = _checked(b_obj)
        b_norm = normalize_text(b_env.final_solution.canonical_text or "")
        b_env.final_solution.sha256 = sha256_hex(b_norm) if b_norm else ""
        transcript.append(b_env.model_dump())

        # Auto-promotion: if both propose the same candidate
        statuses = {a_env.status, b_env.status}
        if a_norm and a_norm == b_norm and statuses.issubset({"PROPOSED","READY_TO_SOLVE"}):
            a_env.status = "SOLVED"; a_env.tags = list(set((a_env.tags or []) + ["[SOLVED]"]))
            b_env.status = "SOLVED"; b_env.tags = list(set((b_env.tags or []) + ["[SOLVED]"]))
            # also update transcript entries
            transcript[-2] = a_env.model_dump()
            transcript[-1] = b_env.model_dump()

        a_ok, _ = _verify_solution(a_env)
        b_ok, _ = _verify_solution(b_env)
        if a_ok and b_ok:
            if a_norm == b_norm and a_env.final_solution.sha256 == b_env.final_solution.sha256:
                return {
                    "status": "CONSENSUS",
                    "rounds": r,
                    "agent_a": a_env.model_dump(),
                    "agent_b": b_env.model_dump(),
                    "transcript": transcript,
                }
            else:
                mismatch_count += 1
                # Arbiter hint (strategy-06 style) after 2 mismatches
                if mismatch_count >= 2:
                    transcript.append({
                        "role": "arbiter",
                        "domain": "controller",
                        "public_message": "Your SOLVED answers do not match. Compare canonical_text strings and converge on a single exact output. Keep JSON valid.",
                        "status": "WORKING"
                    })
    return {
        "status": "NO_CONSENSUS",
        "rounds": max_rounds,
        "transcript": transcript,
        "note": "Max rounds reached without dual SOLVED + identical canonical_text+sha256."
    }

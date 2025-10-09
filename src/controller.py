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
    last_states = {"A": None, "B": None}
    for r in range(1, max_rounds+1):
        # Agent A
        a_obj, a_raw = agent_a.step(task, transcript)
        a_env = _checked(a_obj)
        a_norm = normalize_text(a_env.final_solution.canonical_text or "")
        a_env.final_solution.sha256 = sha256_hex(a_norm) if a_norm else ""
        transcript.append(a_env.model_dump())
        last_states["A"] = a_env.status

        # Agent B
        b_obj, b_raw = agent_b.step(task, transcript)
        b_env = _checked(b_obj)
        b_norm = normalize_text(b_env.final_solution.canonical_text or "")
        b_env.final_solution.sha256 = sha256_hex(b_norm) if b_norm else ""
        transcript.append(b_env.model_dump())
        last_states["B"] = b_env.status

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
        # basic deadlock break: if both NEED_PEER twice in a row, inject a hint next round (left to agents)
        if last_states["A"] == last_states["B"] == "NEED_PEER" and r >= 2:
            # No direct injection; just continue. Real nudges are strategy-dependent.
            pass

    return {
        "status": "NO_CONSENSUS",
        "rounds": max_rounds,
        "transcript": transcript,
        "note": "Max rounds reached without dual SOLVED + identical canonical_text+sha256."
    }

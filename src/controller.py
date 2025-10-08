from __future__ import annotations
from typing import Dict, Any, List, Tuple
from .schemas import Envelope
from .utils import normalize_text, sha256_hex

def _verify_solution(env: Envelope) -> Tuple[bool, str]:
    if not env.is_solved():
        return False, "not solved state or missing [SOLVED]"
    ntext = normalize_text(env.solution.final_text)
    sig = sha256_hex(ntext)
    if not env.solution.solution_signature:
        return False, "signature missing"
    if sig != env.solution.solution_signature:
        return False, "signature mismatch"
    return True, "ok"

def _checked(env_dict: Dict[str, Any]) -> Envelope:
    return Envelope.model_validate(env_dict)

def run_controller(task: str, agent_a, agent_b, max_rounds: int = 8) -> Dict[str, Any]:
    transcript: List[Dict[str, Any]] = []
    raw_traces: List[Dict[str, str]] = []

    for r in range(1, max_rounds + 1):
        a_obj, a_raw = agent_a.step(task, transcript)
        a_env = _checked(a_obj)
        transcript.append(a_env.model_dump())
        raw_traces.append({"agent": agent_a.name, "raw": a_raw})

        b_obj, b_raw = agent_b.step(task, transcript)
        b_env = _checked(b_obj)
        transcript.append(b_env.model_dump())
        raw_traces.append({"agent": agent_b.name, "raw": b_raw})

        a_ok, _ = _verify_solution(a_env)
        b_ok, _ = _verify_solution(b_env)

        if a_ok and b_ok:
            a_sig = a_env.solution.solution_signature
            b_sig = b_env.solution.solution_signature
            if a_sig == b_sig:
                return {
                    "status": "CONSENSUS",
                    "rounds": r,
                    "agent_a": a_env.model_dump(),
                    "agent_b": b_env.model_dump(),
                    "transcript": transcript,
                }
    return {
        "status": "NO_CONSENSUS",
        "rounds": max_rounds,
        "transcript": transcript,
        "note": "Max rounds reached without dual SOLVED + identical signature.",
    }

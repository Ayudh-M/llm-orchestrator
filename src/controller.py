from __future__ import annotations
from typing import Dict, Any, List, Tuple
from .schemas import Envelope
from .utils import normalize_text

def _checked(env_dict: Dict[str, Any]) -> Envelope:
    return Envelope.model_validate(env_dict)

def _verify_solution(env: Envelope) -> Tuple[bool, str]:
    if not env.is_solved():
        return False, "not solved or missing [SOLVED] or canonical_text"
    # canonical_text exists; normalize to compare later
    return True, "ok"

def run_controller(task: str, agent_a, agent_b, max_rounds: int = 8) -> Dict[str, Any]:
    transcript: List[Dict[str, Any]] = []  # public envelopes only

    for r in range(1, max_rounds + 1):
        a_obj, a_raw = agent_a.step(task, transcript)
        a_env = _checked(a_obj)
        transcript.append(a_env.model_dump())

        b_obj, b_raw = agent_b.step(task, transcript)
        b_env = _checked(b_obj)
        transcript.append(b_env.model_dump())

        a_ok, _ = _verify_solution(a_env)
        b_ok, _ = _verify_solution(b_env)

        if a_ok and b_ok:
            a_text = normalize_text(a_env.final_solution.canonical_text)
            b_text = normalize_text(b_env.final_solution.canonical_text)
            if a_text == b_text:
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
        "note": "Max rounds reached without dual SOLVED + identical canonical_text."
    }

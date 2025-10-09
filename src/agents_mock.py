
from __future__ import annotations
from typing import Dict, Any, Tuple
from .schemas import Status

class RuleBasedMock:
    """A trivial mock that immediately solves with a deterministic answer from task string."""
    def __init__(self, answer: str):
        self.answer = answer

    def step(self, task: str, transcript):
        env = {
            "status": "SOLVED",
            "tag": "[SOLVED]",
            "content": {"note": "mock"},
            "final_solution": {"canonical_text": self.answer}
        }
        return env, str(env)

class EchoPeerMock:
    """Solves to the last seen peer SOLVED text if available, else echoes configured answer."""
    def __init__(self, fallback_answer: str):
        self.fallback_answer = fallback_answer

    def step(self, task: str, transcript):
        # find last A envelope if present
        for item in reversed(transcript):
            if item.get("actor") == "A":
                env = item["envelope"]
                if env.get("status") == "SOLVED" and env.get("final_solution"):
                    ans = env["final_solution"]["canonical_text"]
                    break
        else:
            ans = self.fallback_answer
        env = {
            "status": "SOLVED",
            "tag": "[SOLVED]",
            "content": {"note": "echo"},
            "final_solution": {"canonical_text": ans}
        }
        return env, str(env)

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
from .model_loader import load_causal_lm, generate_json_only
from .utils import parse_envelope

@dataclass
class Agent:
    name: str
    role: str
    domain: str
    model_id: str
    system_prompt: str
    seed: int = 7
    max_new_tokens: int = 768

    def __post_init__(self):
        self.tok, self.model = load_causal_lm(self.model_id, seed=self.seed)

    def step(self, task: str, transcript: List[Dict[str, Any]]) -> Tuple[Dict[str,Any], str]:
        user_prompt = task
        raw = generate_json_only(self.tok, self.model, self.system_prompt, user_prompt, max_new_tokens=self.max_new_tokens)
        obj, err = parse_envelope(raw)
        if obj is None:
            # Structured fallback envelope
            fb = {
                "role": self.role,
                "domain": self.domain,
                "task_understanding": "Parse error; requesting clarification.",
                "public_message": "[CONTACT] JSON parse error; please restate or simplify.",
                "artifact": {"type": "results", "content": {}},
                "needs_from_peer": ["Re-send last artifact in simpler structure"],
                "handoff_to": "peer",
                "status": "NEED_PEER",
                "tags": ["[CONTACT]"],
                "request": {"to_peer": "Please restate your last message as valid JSON matching the agreed envelope."},
                "meta": {"strategy_id":"strategy-01"},
                "final_solution": {"canonical_text": "", "sha256": ""}
            }
            return fb, raw
        obj.setdefault("role", self.role)
        obj.setdefault("domain", self.domain)
        # Ensure new protocol keys exist
        obj.setdefault("tags", [])
        obj.setdefault("request", {"to_peer": None})
        obj.setdefault("meta", {"strategy_id":"strategy-01"})
        # Ensure final_solution.sha256 exists
        fs = obj.get("final_solution", {}) or {}
        fs.setdefault("sha256", "")
        obj["final_solution"] = fs
        return obj, raw

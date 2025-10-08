from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any
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
        self.tok, self.mdl = load_causal_lm(self.model_id, seed=self.seed)

    def build_prompt(self, task: str, transcript: List[Dict[str, Any]]):
        tlines = [
            self.system_prompt,
            f"\nYour identity: {self.name} — role: {self.role} — domain: {self.domain}.",
            "\nTask (one line):",
            task.strip(),
            "\nTranscript so far (peer's last public envelopes, newest last):",
        ]
        for e in transcript[-10:]:
            tlines.append(f"- {e.get('role','peer')}: {e.get('public_message','')} status={e.get('status','')}")
        tlines.append("\nReturn ONLY the JSON object described in the protocol.\n")
        return "\n".join(tlines)

    def step(self, task: str, transcript: List[Dict[str, Any]]):
        prompt = self.build_prompt(task, transcript)
        raw = generate_json_only(self.tok, self.mdl, prompt, max_new_tokens=self.max_new_tokens)
        obj, err = parse_envelope(raw)
        if err or not isinstance(obj, dict):
            # fallback minimal envelope
            return {
                "role": self.role,
                "domain": self.domain,
                "task_understanding": "Parse error; requesting clarification.",
                "public_message": "[CONTACT] JSON parse error; please restate or simplify.",
                "artifact": {"type": "results", "content": {}},
                "needs_from_peer": ["Re-send last artifact in simpler structure"],
                "handoff_to": "peer",
                "status": "NEED_PEER",
                "final_solution": {"canonical_text": ""}
            }, raw
        obj.setdefault("role", self.role)
        obj.setdefault("domain", self.domain)
        return obj, raw

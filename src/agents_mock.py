from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
import hashlib

def _deterministic_answer(task: str) -> str:
    # If user embeds a forced answer like <<ANSWER:...>>, honor it
    import re
    m = re.search(r"<<ANSWER:(.+?)>>", task, flags=re.DOTALL)
    if m:
        return m.group(1).strip()
    # else: stable short token derived from task to guarantee both agents converge
    h = hashlib.sha256(task.encode("utf-8")).hexdigest()[:16]
    return f"MOCK_{h}"

@dataclass
class MockAgent:
    name: str
    role: str
    domain: str
    peer_role: str

    def step(self, task: str, transcript: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], str]:
        # Simple 2-turn dance: first turn asks peer, second turn solves with the same canonical_text
        prior_agent_msgs = [t for t in transcript if t.get("role") == self.role]
        tag = "[CONTACT]" if len(prior_agent_msgs) == 0 else "[SOLVED]"
        status = "PROPOSED" if tag == "[CONTACT]" else "SOLVED"
        canonical = _deterministic_answer(task) if tag == "[SOLVED]" else ""

        env = {
            "role": self.role,
            "domain": self.domain,
            "task_understanding": "mock_run",
            "public_message": tag,
            "artifact": {"type":"results","content":{}},
            "needs_from_peer": [] if tag == "[SOLVED]" else ["peer review"],
            "handoff_to": self.peer_role,
            "status": status,
            "final_solution": {"canonical_text": canonical, "sha256": ""},
            "tags": [tag],
            "request": {"to_peer": self.peer_role},
            "meta": {"generator":"MockAgent","token_estimate":{"prompt":0,"gen":0}},
            "scratch": {}
        }
        return env, json_dumps(env)

def json_dumps(obj: Dict[str, Any]) -> str:
    # Deterministic JSON string for visibility
    import json
    return json.dumps(obj, separators=(',', ':'), ensure_ascii=False)

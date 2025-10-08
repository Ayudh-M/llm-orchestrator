from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any
from .model_loader import load_causal_lm, generate_json_only
from .utils import parse_envelope

AGENT_SYSTEM_PROMPT = (
    "You are a helpful expert agent. You must respond with **ONLY** a compact JSON object\n"
    "matching this schema (no extra text, no explanations):\n\n"
    "{\n"
    "  \"agent\": \"<your-role>\",\n"
    "  \"status\": \"WORKING|ASKING|SOLVED\",\n"
    "  \"public_message\": \"A short message for your peer; include [CONTACT] if you need them. When done, include [SOLVED].\",\n"
    "  \"solution\": {\n"
    "    \"final_text\": \"If SOLVED, put the verbatim final solution here; otherwise empty string.\",\n"
    "    \"solution_signature\": \"If SOLVED, sha256 of normalized final_text; otherwise empty.\"\n"
    "  }\n"
    "}\n\n"
    "Never reveal chain-of-thought or private notes. Keep messages concise."
)

@dataclass
class Agent:
    name: str
    role: str
    model_id: str
    seed: int = 7
    max_new_tokens: int = 512

    def __post_init__(self):
        self.tok, self.mdl = load_causal_lm(self.model_id, seed=self.seed)

    def build_prompt(self, task: str, transcript: List[Dict[str, Any]]):
        tlines = [
            AGENT_SYSTEM_PROMPT,
            f"\nYour role: {self.role} (agent id: {self.name}).",
            "\nTask (one line):",
            task.strip(),
            "\nTranscript so far (public envelopes, most recent last):",
        ]
        for e in transcript[-10:]:
            tlines.append(f"- {e['agent']}: {e['public_message']} status={e['status']}")
        tlines.append("\nReturn ONLY the JSON envelope.\n")
        return "\n".join(tlines)

    def step(self, task: str, transcript: List[Dict[str, Any]]):
        prompt = self.build_prompt(task, transcript)
        raw = generate_json_only(self.tok, self.mdl, prompt, max_new_tokens=self.max_new_tokens)
        obj, err = parse_envelope(raw)
        if err or not isinstance(obj, dict):
            return {
                "agent": self.name,
                "status": "ASKING",
                "public_message": f"[CONTACT] JSON parse error; please restate or simplify. ({err})",
                "solution": {"final_text": "", "solution_signature": ""},
            }, raw
        obj.setdefault("agent", self.name)
        return obj, raw

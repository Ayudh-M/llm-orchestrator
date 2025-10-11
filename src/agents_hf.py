from __future__ import annotations
import json, re
from typing import Any, Dict, List, Optional
from .model_loader import generate_json_only
from .strategies import Strategy

JSON_GUIDE = """You are one of two collaborating agents. Respond with a SINGLE JSON object ONLY.
Schema:
{
  "tag": "[CONTACT]" or "[SOLVED]",
  "status": "WORKING" | "NEED_PEER" | "PROPOSED" | "READY_TO_SOLVE" | "SOLVED",
  "content": { ...freeform keys... },
  "final_solution": {"canonical_text": "<string>", "sha256": "<64 hex>"} // include ONLY when status is SOLVED
}
No preamble, no backticks, no commentary — just the JSON object.
"""

def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None

class HFJsonAgent:
    def __init__(self, model, tokenizer, role_name: str, role_instructions: str, strategy: Strategy):
        self.model = model
        self.tokenizer = tokenizer
        self.role_name = role_name
        self.role_instructions = role_instructions
        self.strategy = strategy

    def _messages(self, task: str, transcript: List[Dict[str, Any]]) -> List[Dict[str,str]]:
        sys = f"Role: {self.role_name}\n{self.role_instructions}\n"
        if getattr(self.strategy, "json_only", False):
            sys += "\n" + JSON_GUIDE
        if getattr(self.strategy, "short_utterances", False):
            sys += "\nKeep messages short."

        peer_context = ""
        if transcript:
            last = transcript[-1]
            peer_context = json.dumps(last.get("envelope", {}), ensure_ascii=False)

        usr = f"Task: {task}\nPeer context: {peer_context}\nReturn ONLY the JSON object per schema."
        return [{"role":"system","content":sys}, {"role":"user","content":usr}]

    def step(self, task: str, transcript: List[Dict[str, Any]]):
        msgs = self._messages(task, transcript)
        raw = generate_json_only(
            self.model, self.tokenizer, msgs,
            max_new_tokens=256,
            temperature=(getattr(self.strategy, "decoding", None) or {}).get("temperature", 0.2)
        )
        env = _extract_json(raw) or {"status":"WORKING", "tag":"[CONTACT]", "content":{"note":"fallback"}}
        return env, raw

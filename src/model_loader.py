
from __future__ import annotations
from typing import Dict, Any, List

def load_causal_lm(model_id: str):
    raise RuntimeError("HF model loading not available in this environment. Use --mock for local tests.")

def build_inputs(system: str, user: str) -> List[Dict[str, str]]:
    return [{"role":"system","content":system},{"role":"user","content":user}]

def _render_chat(messages: List[Dict[str, str]]) -> str:
    # naive render
    return "\n".join([f"{m['role'].upper()}: {m['content']}" for m in messages])

def generate_json_only(model, tokenizer, messages, max_new_tokens=256, temperature=0.0) -> str:
    # placeholder; real implementation would call transformers.generate
    raise RuntimeError("Text generation not available here. Use mocks.")

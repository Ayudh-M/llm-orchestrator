
from __future__ import annotations
import json, re
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

DTYPE_MAP = {
    "bfloat16": torch.bfloat16,
    "float16": torch.float16,
    "fp16": torch.float16,
    "float32": torch.float32,
    "fp32": torch.float32,
}

def _safe_json_extract(text: str):
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"\{(?:[^{}]|\{[^{}]*\})*\}", text, re.DOTALL)
    if m:
        frag = m.group(0)
        try:
            return json.loads(frag)
        except Exception:
            return None
    return None

@dataclass
class HFChatAgent:
    system_prompt: str
    model_id: str
    dtype: str = "bfloat16"
    max_tokens: int = 768
    temperature: float = 0.7
    top_p: float = 0.95

    def __post_init__(self):
        torch_dtype = DTYPE_MAP.get(self.dtype.lower(), torch.bfloat16)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id, use_fast=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            torch_dtype=torch_dtype,
            device_map="auto"
        )

    def build_prompt(self, messages: List[Dict[str, str]]) -> str:
        try:
            return self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
        except Exception:
            # Fallback for models without chat_template
            parts = []
            for m in messages:
                role = m.get("role", "user")
                content = (m.get("content") or "").strip()
                if role == "system":
                    parts.append(content)
                elif role == "user":
                    parts.append(f"User: {content}")
                elif role == "assistant":
                    parts.append(f"Assistant: {content}")
            parts.append("Assistant:")
            return "\n".join(parts)

    def generate(self, prompt: str) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            out = self.model.generate(
                **inputs,
                max_new_tokens=self.max_tokens,
                do_sample=True,
                temperature=self.temperature,
                top_p=self.top_p,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
        text = self.tokenizer.decode(out[0], skip_special_tokens=True)
        if prompt in text:
            text = text[len(prompt):]
        return text.strip()

    def step(self, task_text: str, peer_context: Dict[str, Any], schema_hint: Optional[str]) -> Dict[str, Any]:
        schema_guard = schema_hint or '{"tag":"[CONTACT]","status":"WORKING","content":{"note":"fallback"}}'

        sys_msg = self.system_prompt.strip()
        user_msg = f"""
Task: {task_text}

You are collaborating with a peer agent. Peer context (for your awareness):
{json.dumps(peer_context, ensure_ascii=False)}

Respond with ONLY one JSON object that roughly follows:
{schema_guard}

If you have a final answer, include:
"final_solution": {{"canonical_text": "<your final text here>"}},
and set "status": "SOLVED".
No markdown, no extra text beyond the single JSON object.
""".strip()

        messages = [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": user_msg},
        ]
        prompt = self.build_prompt(messages)
        raw = self.generate(prompt)

        env = _safe_json_extract(raw) or {
            "tag": "[CONTACT]",
            "status": "WORKING",
            "content": {"text": raw[:2000]}
        }
        return env

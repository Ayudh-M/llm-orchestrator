\
import json, hashlib, re
from typing import Dict, Any, Optional
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class HFChatAgent:
    def __init__(self, model_name: str, dtype_str: str = "bfloat16"):
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=False)
        _dtype = {"bfloat16": torch.bfloat16, "float16": torch.float16}.get(dtype_str, None)
        # Use `dtype` (preferred in newer Transformers)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            dtype=_dtype,
            trust_remote_code=False,
        )
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

    def build_prompt(self, task_text: str, peer_context: Dict[str, Any], schema_hint: str) -> str:
        system = (
            "You are an agent in a 2-agent orchestrator.\n"
            "Return ONLY one compact JSON object with keys exactly: "
            '{"tag": "...", "status": "...", "content": {...}, '
            '"final_solution": {"canonical_text": "...", "sha256": null}}\n'
            "No prose, no code fences, no extra keys. " + schema_hint
        )
        user = (
            f"Task: {task_text}\n"
            f"Peer context: {json.dumps(peer_context, ensure_ascii=False)}\n"
            "Return ONLY the JSON object per schema."
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        return prompt

    def generate_once(self, prompt: str, max_new_tokens: int = 256) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        out = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=0.0,
            top_p=1.0,
            eos_token_id=self.tokenizer.eos_token_id,
            pad_token_id=self.tokenizer.pad_token_id,
        )
        return self.tokenizer.decode(out[0], skip_special_tokens=True)

    @staticmethod
    def extract_first_json(s: str) -> Optional[Dict[str, Any]]:
        start = s.find("{")
        if start == -1:
            return None
        depth = 0
        for i in range(start, len(s)):
            if s[i] == "{":
                depth += 1
            elif s[i] == "}":
                depth -= 1
                if depth == 0:
                    chunk = s[start:i+1]
                    try:
                        return json.loads(chunk)
                    except Exception:
                        break
        import re
        for m in re.finditer(r"\{.*\}", s, flags=re.DOTALL):
            try:
                return json.loads(m.group(0))
            except Exception:
                continue
        return None

    @staticmethod
    def canonicalize(obj: Dict[str, Any]) -> Dict[str, Any]:
        obj.setdefault("tag", "[CONTACT]")
        obj.setdefault("status", "WORKING")
        obj.setdefault("content", {})
        obj.setdefault("final_solution", {"canonical_text": None, "sha256": None})
        if "canonical_text" not in obj["final_solution"]:
            obj["final_solution"]["canonical_text"] = None
        if "sha256" not in obj["final_solution"]:
            obj["final_solution"]["sha256"] = None
        ct = obj["final_solution"].get("canonical_text")
        if isinstance(ct, str) and (obj["final_solution"].get("sha256") in (None, "", "null")):
            obj["final_solution"]["sha256"] = hashlib.sha256(ct.encode("utf-8")).hexdigest()
        return obj

    def step(self, task_text: str, peer_context: Dict[str, Any], schema_hint: str) -> Dict[str, Any]:
        prompt = self.build_prompt(task_text, peer_context, schema_hint)
        raw = self.generate_once(prompt)
        parsed = self.extract_first_json(raw)
        if not parsed:
            return {"tag": "[CONTACT]", "status": "WORKING", "content": {"note": "fallback"}, "final_solution": {"canonical_text": None, "sha256": None}}
        return self.canonicalize(parsed)

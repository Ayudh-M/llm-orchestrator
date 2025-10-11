from __future__ import annotations
from typing import List, Dict, Any, Optional
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

def load_causal_lm(model_id: str, dtype: str = "bfloat16"):
    """Load a causal LM + tokenizer with a simple device_map=auto setup."""
    if dtype == "bfloat16":
        torch_dtype = torch.bfloat16
    elif dtype == "float16":
        torch_dtype = torch.float16
    elif dtype == "float32":
        torch_dtype = torch.float32
    else:
        torch_dtype = None

    tok = AutoTokenizer.from_pretrained(model_id, use_fast=True)
    mdl = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch_dtype,
        device_map="auto",
    )
    return mdl, tok

def _render_chat(tokenizer, messages: List[Dict[str,str]]) -> str:
    """Use tokenizer's chat template if available, else fall back to a simple format."""
    if hasattr(tokenizer, "apply_chat_template") and getattr(tokenizer, "chat_template", None):
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    out = []
    for m in messages:
        role = m.get("role", "user").upper()
        out.append(f"{role}: {m['content']}")
    out.append("ASSISTANT:")
    return "\n".join(out)

def generate_json_only(model, tokenizer, messages: List[Dict[str,str]],
                       max_new_tokens: int = 256, temperature: float = 0.2) -> str:
    prompt = _render_chat(tokenizer, messages)
    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    do_sample = temperature is not None and temperature > 0.0
    gen = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=do_sample,
        temperature=temperature if do_sample else None,
        pad_token_id=tokenizer.eos_token_id,
    )
    gen_ids = gen[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(gen_ids, skip_special_tokens=True)

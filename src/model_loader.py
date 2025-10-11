from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
import os, torch, random
from transformers import AutoTokenizer, AutoModelForCausalLM

def _resolve_dtype(dtype: str | None):
    if dtype is None:
        return None
    d = dtype.lower()
    if d in ("bfloat16","bf16"):
        return torch.bfloat16
    if d in ("float16","fp16"):
        return torch.float16
    if d in ("float32","fp32"):
        return torch.float32
    return None

def _maybe_set_seed(seed: Optional[int]):
    if seed is None:
        return
    try:
        import numpy as np
        np.random.seed(seed)
    except Exception:
        pass
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def load_causal_lm(model_id: str, dtype: str = "bfloat16", seed: Optional[int] = None, cache_dir: Optional[str] = None) -> Tuple[Any, Any]:
    """
    Load a causal LM + tokenizer. Returns (tokenizer, model).
    - dtype: 'bfloat16' | 'float16' | 'float32'
    - seed: for deterministic-ish generation (sets torch/python/numpy seeds)
    - cache_dir: optional HF cache override (will also honor HF_HOME/TRANSFORMERS_CACHE envs)
    """
    _maybe_set_seed(seed)
    torch_dtype = _resolve_dtype(dtype)

    tok = AutoTokenizer.from_pretrained(model_id, use_fast=True, cache_dir=cache_dir)
    # Some base models lack a pad token; use EOS as pad to avoid warnings
    if tok.pad_token_id is None and tok.eos_token_id is not None:
        tok.pad_token = tok.eos_token

    mdl = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch_dtype,
        device_map="auto",
        cache_dir=cache_dir,
    )
    return tok, mdl

def _render_chat(tokenizer, messages: List[Dict[str,str]]) -> str:
    """Use tokenizer's chat template if available, else fall back to a simple format."""
    if hasattr(tokenizer, "apply_chat_template") and getattr(tokenizer, "chat_template", None):
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    out = []
    for m in messages:
        role = m.get("role", "user").upper()
        out.append(f"{role}: {m['content']}")
    out.append("ASSISTANT:")
    return "\\n".join(out)

def build_inputs(system_prompt: str, user_prompt: str) -> List[Dict[str,str]]:
    """Construct a 2-message chat: system + user."""
    return [
        {"role":"system","content":system_prompt},
        {"role":"user","content":user_prompt},
    ]

def _generate(tokenizer, model, messages: List[Dict[str,str]], max_new_tokens: int = 256, temperature: float = 0.2) -> str:
    prompt = _render_chat(tokenizer, messages)
    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    do_sample = temperature is not None and temperature > 0.0
    gen = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=do_sample,
        temperature=(temperature if do_sample else None),
        pad_token_id=tokenizer.eos_token_id,
    )
    gen_ids = gen[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(gen_ids, skip_special_tokens=True)

def generate_json_only(tokenizer, model, system_prompt: str | List[Dict[str,str]], user_prompt: Optional[str] = None,
                       max_new_tokens: int = 256, temperature: float = 0.2) -> str:
    """
    Compatibility wrapper used by different agent flavors:
    - If system_prompt is a list[dict], treat it as full 'messages' directly.
    - Else, build [system, user] with the provided strings.
    """
    if isinstance(system_prompt, list):
        messages = system_prompt  # already in chat form
    else:
        messages = build_inputs(system_prompt, user_prompt or "")
    return _generate(tokenizer, model, messages, max_new_tokens=max_new_tokens, temperature=temperature)

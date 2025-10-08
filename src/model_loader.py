from __future__ import annotations
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, set_seed

def load_causal_lm(model_id: str, seed: int = 7):
    set_seed(seed)
    dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
    tok = AutoTokenizer.from_pretrained(model_id, use_fast=True)
    if tok.pad_token_id is None:
        tok.pad_token_id = tok.eos_token_id
    mdl = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=dtype,
        device_map="auto",
    )
    return tok, mdl

def generate_json_only(tok, mdl, prompt: str, max_new_tokens: int = 768, temperature: float = 0.6, top_p: float = 0.9) -> str:
    inputs = tok(prompt, return_tensors="pt").to(mdl.device)
    with torch.no_grad():
        out = mdl.generate(
            **inputs,
            do_sample=True,
            temperature=temperature,
            top_p=top_p,
            max_new_tokens=max_new_tokens,
            pad_token_id=tok.pad_token_id,
            eos_token_id=tok.eos_token_id,
        )
    text = tok.decode(out[0], skip_special_tokens=True)
    return text[len(prompt):].strip() if text.startswith(prompt) else text

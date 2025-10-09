from __future__ import annotations
import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, set_seed

def load_causal_lm(model_id: str, seed: int = 7):
    set_seed(seed)
    dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
    tok = AutoTokenizer.from_pretrained(model_id, use_fast=True)
    if tok.pad_token_id is None and tok.eos_token_id is not None:
        tok.pad_token_id = tok.eos_token_id
    mdl = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=dtype,
        device_map="auto",
    )
    return tok, mdl

def build_inputs(tok, system_prompt: str, user_prompt: str):
    # Prefer chat template if available
    try:
        messages = [{"role":"system","content":system_prompt},
                    {"role":"user","content":user_prompt}]
        text = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        return tok(text, return_tensors="pt")
    except Exception:
        # Fallback to plain concatenation
        text = system_prompt.strip() + "\n\n" + user_prompt.strip()
        return tok(text, return_tensors="pt")

def generate_json_only(tok, mdl, system_prompt: str, user_prompt: str,
                       max_new_tokens: int = 768, temperature: float = 0.3, top_p: float = 0.9) -> str:
    do_sample = os.getenv("GEN_SAMPLE", "0") not in ("0","false","False","NO")
    inputs = build_inputs(tok, system_prompt, user_prompt).to(mdl.device)
    with torch.no_grad():
        out = mdl.generate(
            **inputs,
            do_sample=do_sample,
            temperature=temperature,
            top_p=top_p,
            max_new_tokens=max_new_tokens,
            pad_token_id=tok.pad_token_id,
            eos_token_id=tok.eos_token_id,
        )
    text = tok.decode(out[0], skip_special_tokens=True)
    # If chat template was used, model output comes after the last assistant prefix; keep as-is.
    return text

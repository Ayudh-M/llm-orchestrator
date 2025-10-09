from __future__ import annotations
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

def _render_chat(tok, system_prompt: str, user_prompt: str) -> str:
    msgs = [{"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}]
    return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)

def build_inputs(tok, system_prompt: str, user_prompt: str):
    prompt = _render_chat(tok, system_prompt, user_prompt)
    return tok(prompt, return_tensors="pt")

def generate_json_only(tok, mdl, system_prompt: str, user_prompt: str, max_new_tokens: int = 512,
                       do_sample: bool = False, temperature: float = 0.0, top_p: float = 1.0) -> str:
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
    return text

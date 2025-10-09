from __future__ import annotations
import os, json
from typing import List, Dict

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROLESETS_DIR = os.path.join(REPO_ROOT, "rolesets")
PACKS_DIR = os.path.join(ROLESETS_DIR, "packs")
STRATEGIES_DIR = os.path.join(REPO_ROOT, "strategies")
GLOBAL_PROTOCOL = os.path.join(ROLESETS_DIR, "_GLOBAL_PROTOCOL.md")

def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def _load_struct(path: str):
    if path.endswith(".json"):
        return json.loads(_read_text(path))
    raise ValueError(f"Unsupported roleset format: {path}")

def _roleset_path(name_or_path: str) -> str:
    if os.path.exists(name_or_path):
        return os.path.abspath(name_or_path)
    cand = os.path.join(ROLESETS_DIR, name_or_path if name_or_path.endswith(".json") else name_or_path + ".json")
    if os.path.exists(cand):
        return cand
    raise FileNotFoundError(f"Roleset '{name_or_path}' not found")

def _build_system_prompt(pack_name: str, strategy_name: str | None) -> str:
    parts = []
    if os.path.exists(GLOBAL_PROTOCOL):
        parts.append(_read_text(GLOBAL_PROTOCOL))
    if strategy_name:
        sp = os.path.join(STRATEGIES_DIR, f"{strategy_name}.md")
        if os.path.exists(sp):
            parts.append(_read_text(sp))
    pp = os.path.join(PACKS_DIR, f"{pack_name}.md")
    if os.path.exists(pp):
        parts.append(_read_text(pp))
    return "\n\n".join(parts)

def load_roleset(name_or_path: str, strategy_name: str | None = None) -> List[Dict[str, str]]:
    path = _roleset_path(name_or_path)
    data = _load_struct(path)
    roles = []
    for agent in data.get("agents", []):
        sp = _build_system_prompt(agent.get("pack",""), strategy_name or "strategy-01")
        roles.append({
            "name": agent.get("name","agent"),
            "role": agent.get("role",""),
            "domain": agent.get("domain",""),
            "model": agent.get("model","mistralai/Mistral-7B-Instruct-v0.2"),
            "system_prompt": sp,
        })
    if len(roles) != 2:
        raise ValueError("Roleset must define exactly two agents")
    return roles

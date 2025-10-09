from __future__ import annotations
import os, json
from typing import List, Dict

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROLESETS_DIR = os.path.join(REPO_ROOT, "rolesets")
PACKS_DIR = os.path.join(ROLESETS_DIR, "packs")
STRATEGIES_DIR = os.path.join(REPO_ROOT, "strategies")
DEFAULT_STRATEGY = "strategy-01.md"

def _read(p: str) -> str:
    with open(p, "r", encoding="utf-8") as f:
        return f.read().strip()

def _load_struct(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        txt = f.read()
    if path.endswith((".yml",".yaml")):
        if not yaml:
            raise RuntimeError("PyYAML required for YAML rolesets")
        return yaml.safe_load(txt)
    return json.loads(txt)

def _assemble_system_prompt(pack: str | None, strategy_name: str | None) -> str:
    # Strategy text comes first; pack text appended.
    if strategy_name:
        s_path = os.path.join(STRATEGIES_DIR, strategy_name if strategy_name.endswith(".md") else f"{strategy_name}.md")
        if not os.path.exists(s_path):
            raise FileNotFoundError(f"Strategy '{strategy_name}' not found under strategies/")
    else:
        s_path = os.path.join(STRATEGIES_DIR, DEFAULT_STRATEGY)
    base = _read(s_path)

    if pack:
        pack_path = os.path.join(PACKS_DIR, f"{pack}.md")
        if os.path.exists(pack_path):
            base += "\n\n" + _read(pack_path)
    return base

def load_roleset(name_or_path: str, strategy_name: str | None = None) -> List[Dict[str, str]]:
    # Resolve JSON/YAML
    if os.path.exists(name_or_path):
        data = _load_struct(name_or_path)
    else:
        for ext in (".json",".yaml",".yml"):
            p = os.path.join(ROLESETS_DIR, name_or_path + ext)
            if os.path.exists(p):
                data = _load_struct(p)
                break
        else:
            raise FileNotFoundError(f"Roleset '{name_or_path}' not found in {ROLESETS_DIR}")
    agents = data.get("agents", [])
    if not isinstance(agents, list) or len(agents) != 2:
        raise ValueError("This controller expects exactly 2 agents in the roleset")

    out = []
    for a in agents:
        name = a.get("name")
        role = a.get("role")
        domain = a.get("domain", role)
        model = a.get("model")
        pack = a.get("pack")  # optional string referencing packs/*.md
        system_prompt = _assemble_system_prompt(pack, strategy_name)
        if not all([name, role, model]):
            raise ValueError("Each agent must include name, role, model")
        out.append({
            "name": name,
            "role": role,
            "domain": domain,
            "model": model,
            "system_prompt": system_prompt
        })
    return out

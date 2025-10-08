from __future__ import annotations
import os, json
from typing import List, Dict

try:
    import yaml  # type: ignore
except Exception:
    yaml = None  # optional

def _repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def _rolesets_dir() -> str:
    return os.path.join(_repo_root(), "rolesets")

def _load_file(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        txt = f.read()
    if path.endswith((".yml", ".yaml")):
        if not yaml:
            raise RuntimeError("PyYAML not installed but a YAML roleset was provided")
        return yaml.safe_load(txt)
    return json.loads(txt)

def load_roleset(name_or_path: str) -> List[Dict[str, str]]:
    if os.path.exists(name_or_path):
        data = _load_file(name_or_path)
    else:
        base = name_or_path
        rsdir = _rolesets_dir()
        candidates = [
            os.path.join(rsdir, base + ".json"),
            os.path.join(rsdir, base + ".yaml"),
            os.path.join(rsdir, base + ".yml"),
        ]
        for c in candidates:
            if os.path.exists(c):
                data = _load_file(c)
                break
        else:
            raise FileNotFoundError(f"Roleset '{name_or_path}' not found in {rsdir}")
    agents = data.get("agents", [])
    if not isinstance(agents, list) or len(agents) != 2:
        raise ValueError("This controller expects exactly 2 agents in the roleset")
    for a in agents:
        if not all(k in a for k in ("name", "role", "model")):
            raise ValueError("Each agent must have name, role, model")
    return agents


from __future__ import annotations
import json, yaml
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "prompts" / "registry.yaml"

def _load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}

def load_registry() -> Dict[str, Any]:
    if not REGISTRY.exists():
        raise FileNotFoundError(f"Registry not found: {REGISTRY}")
    data = _load_yaml(REGISTRY)
    if "scenarios" not in data or not isinstance(data["scenarios"], dict):
        raise ValueError("Registry must contain a 'scenarios' mapping.")
    return data

def load_strategy(name: str) -> Dict[str, Any]:
    path = ROOT / "prompts" / "strategies" / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Strategy file not found: {path}")
    return _load_yaml(path)

def load_roleset(path_str: str) -> Dict[str, Any]:
    path = (ROOT / path_str).resolve()
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(text)
    return json.loads(text)

def get_scenario(sid: str) -> Dict[str, Any]:
    reg = load_registry()
    try:
        return reg["scenarios"][sid]
    except KeyError as e:
        raise KeyError(f"Scenario '{sid}' not found in {REGISTRY}") from e

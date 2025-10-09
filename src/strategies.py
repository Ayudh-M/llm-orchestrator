
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class Strategy:
    name: str
    json_only: bool = True
    allow_cot: bool = False
    use_grammar: bool = False
    decoding: Dict[str, Any] = None
    max_turns: int = 12
    short_utterances: bool = True

REGISTRY = {
    "S1": Strategy("S1", json_only=True, allow_cot=False, decoding={"temperature":0.0}),
    "S2": Strategy("S2", json_only=True, allow_cot=True, decoding={"temperature":0.3}),
    "S3": Strategy("S3", json_only=True, allow_cot=False, decoding={"temperature":0.0}),
    "S4": Strategy("S4", json_only=True, allow_cot=True, decoding={"temperature":0.2}),
    "S5": Strategy("S5"),
    "S6": Strategy("S6"),
    "S7": Strategy("S7"),
    "S8": Strategy("S8"),
    "S9": Strategy("S9"),
    "S10": Strategy("S10"),
}

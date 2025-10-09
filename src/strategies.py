from dataclasses import dataclass

@dataclass
class StrategyCfg:
    id: str
    greedy: bool = True
    json_only: bool = True
    allow_cot: bool = False
    k_samples: int = 1
    max_new_tokens: int = 512

REGISTRY = {
    "strategy-01": StrategyCfg("strategy-01", greedy=True, json_only=True, allow_cot=False, k_samples=1, max_new_tokens=256),
    "strategy-03": StrategyCfg("strategy-03", greedy=False, json_only=True, allow_cot=True, k_samples=1, max_new_tokens=512),
    "strategy-05": StrategyCfg("strategy-05", greedy=False, json_only=True, allow_cot=False, k_samples=3, max_new_tokens=384),
}

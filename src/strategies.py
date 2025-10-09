from dataclasses import dataclass

@dataclass
class StrategyCfg:
    id: str
    greedy: bool = True
    json_only: bool = True
    allow_cot: bool = False

REGISTRY = {
    "strategy-01": StrategyCfg("strategy-01", greedy=True, json_only=True, allow_cot=False),
    "strategy-03": StrategyCfg("strategy-03", greedy=False, json_only=True, allow_cot=True),
}

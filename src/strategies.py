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
    # Strict JSON-only, greedy, no CoT (baseline)
    "strategy-01": StrategyCfg("strategy-01", greedy=True,  json_only=True, allow_cot=False, k_samples=1, max_new_tokens=256),
    # Greedy JSON-only but allow CoT in freeform fields (same decode as 03 for now)
    "strategy-02": StrategyCfg("strategy-02", greedy=True,  json_only=True, allow_cot=True,  k_samples=1, max_new_tokens=256),
    # Sampled JSON-only, allow CoT (temperature path)
    "strategy-03": StrategyCfg("strategy-03", greedy=False, json_only=True, allow_cot=True,  k_samples=1, max_new_tokens=512),
    # Sampled JSON-only, allow CoT, shorter outputs (template of 03)
    "strategy-04": StrategyCfg("strategy-04", greedy=False, json_only=True, allow_cot=True,  k_samples=1, max_new_tokens=384),
    # k-sample self-consistency (pick first SOLVED else first)
    "strategy-05": StrategyCfg("strategy-05", greedy=False, json_only=True, allow_cot=False, k_samples=3, max_new_tokens=384),
    # Arbiter-hint after mismatches (controller reads id only; decode like 01)
    "strategy-06": StrategyCfg("strategy-06", greedy=True,  json_only=True, allow_cot=False, k_samples=1, max_new_tokens=256),
    # Longer outputs allowed (for code/SQL); greedy
    "strategy-07": StrategyCfg("strategy-07", greedy=True,  json_only=True, allow_cot=False, k_samples=1, max_new_tokens=768),
    # Temperature sampling, short outputs
    "strategy-08": StrategyCfg("strategy-08", greedy=False, json_only=True, allow_cot=False, k_samples=1, max_new_tokens=256),
    # Temperature + k=3
    "strategy-09": StrategyCfg("strategy-09", greedy=False, json_only=True, allow_cot=False, k_samples=3, max_new_tokens=256),
    # Freeform (non-JSON) prototype OFF by default; here still JSON-only for safety (you can flip later)
    "strategy-10": StrategyCfg("strategy-10", greedy=True,  json_only=True, allow_cot=True,  k_samples=1, max_new_tokens=512),
}

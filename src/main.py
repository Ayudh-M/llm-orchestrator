
from __future__ import annotations
import argparse, json, time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List

from template_loader import get_scenario, load_roleset, load_strategy
from agent import HFChatAgent

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
RUNS.mkdir(exist_ok=True)

def _now_stamp() -> str:
    return time.strftime("%Y%m%d-%H%M%S")

def _pick_roles(roleset: Dict[str, Any]):
    roleA = (roleset.get("A") or {}).get("system")
    roleB = (roleset.get("B") or {}).get("system")
    if not roleA or not roleB:
        raise ValueError("Roleset must contain keys 'A' and 'B' with 'system' prompts.")
    return roleA, roleB

def build_agents(roleset: Dict[str, Any], model_a: str, model_b: str, dtype: str):
    roleA, roleB = _pick_roles(roleset)
    A = HFChatAgent(system_prompt=roleA, model_id=model_a, dtype=dtype)
    B = HFChatAgent(system_prompt=roleB, model_id=model_b, dtype=dtype)
    return A, B

def run_contact_strategy(task_text: str, schema_hint: Optional[str],
                         roleset: Dict[str, Any], model_a: str, model_b: str, dtype: str,
                         strategy: Dict[str, Any], max_rounds: int, stop_when: List[str],
                         out_prefix: str) -> Dict[str, Any]:

    A, B = build_agents(roleset, model_a, model_b, dtype)

    transcript = []
    env_a = {"tag": "[CONTACT]", "status": "WORKING", "content": {"note": "start"}}
    env_b = {"tag": "[CONTACT]", "status": "WORKING", "content": {"note": "start"}}

    def is_stop(env: Dict[str, Any]) -> bool:
        if env.get("status") in stop_when:
            return True
        fs = env.get("final_solution") or {}
        return bool(fs.get("canonical_text"))

    for r in range(1, max_rounds + 1):
        env_a = A.step(task_text, env_b, schema_hint)
        transcript.append({"t": r, "actor": "A", "envelope": env_a})
        if is_stop(env_a):
            break

        env_b = B.step(task_text, env_a, schema_hint)
        transcript.append({"t": r, "actor": "B", "envelope": env_b})
        if is_stop(env_b):
            break

    def extract_text(env: Dict[str, Any]) -> Optional[str]:
        return (env.get("final_solution") or {}).get("canonical_text") \
            or (env.get("content") or {}).get("canonical_text") \
            or (env.get("content") or {}).get("text")

    winner = env_a if is_stop(env_a) else (env_b if is_stop(env_b) else None)
    status = "SOLVED" if winner else "NO_CONSENSUS"
    canonical = extract_text(winner) if winner else None

    out = {
        "status": status,
        "rounds": len(transcript),
        "transcript": transcript
    }
    (RUNS / f"{out_prefix}.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", type=str, help="Scenario id from prompts/registry.yaml")
    ap.add_argument("--task", type=str, help="Legacy task text")
    ap.add_argument("--roleset", type=str, help="Legacy roleset path")
    ap.add_argument("--strategy", type=str, default="S1")
    ap.add_argument("--model-a", type=str)
    ap.add_argument("--model-b", type=str)
    ap.add_argument("--dtype", type=str, default="bfloat16")
    ap.add_argument("--schema-hint", type=str)
    args = ap.parse_args()

    if args.scenario:
        sc = get_scenario(args.scenario)
        task_text   = sc["task_text"]
        roleset     = load_roleset(sc["roleset"])
        strategy    = load_strategy(sc.get("strategy", "S1"))
        schema_hint = sc.get("schema_hint")
        model_a     = args.model_a or sc["models"]["a"]
        model_b     = args.model_b or sc["models"]["b"]
        dtype       = args.dtype or sc.get("dtype", "bfloat16")
        max_rounds  = sc.get("max_rounds", strategy.get("max_rounds", 8))
        stop_when   = sc.get("stop_when", strategy.get("stop_when", ["SOLVED"]))
        out_prefix  = f"{_now_stamp()}_{args.scenario}"
    else:
        if not args.task or not args.roleset:
            raise SystemExit("Provide --scenario OR (--task AND --roleset).")
        task_text   = args.task
        roleset     = load_roleset(args.roleset)
        strategy    = load_strategy(args.strategy)
        schema_hint = args.schema_hint
        model_a     = args.model_a or "mistralai/Mistral-7B-Instruct-v0.2"
        model_b     = args.model_b or "mistralai/Mistral-7B-Instruct-v0.2"
        dtype       = args.dtype
        max_rounds  = strategy.get("max_rounds", 8)
        stop_when   = strategy.get("stop_when", ["SOLVED"])
        out_prefix  = f"{_now_stamp()}_legacy"

    out = run_contact_strategy(task_text, schema_hint, roleset, model_a, model_b,
                               dtype, strategy, max_rounds, stop_when, out_prefix)

    final_env = out.get("transcript", [])[-1]["envelope"] if out.get("transcript") else {}
    txt = (final_env.get("final_solution", {}) or {}).get("canonical_text") \
          or (final_env.get("content", {}) or {}).get("canonical_text") \
          or (final_env.get("content", {}) or {}).get("text") \
          or ""
    print("\\n=== FINAL TEXT ===\\n" + txt)

if __name__ == "__main__":
    main()

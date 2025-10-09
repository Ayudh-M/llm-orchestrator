from __future__ import annotations
import argparse, json, os, time
from dotenv import load_dotenv
from rich import print
from .agents import Agent
from .controller import run_controller
from .roleset_loader import load_roleset
from .judges import judge_auto
from .logger import append_jsonl
from datetime import datetime

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", type=str, required=True)
    ap.add_argument("--models", type=str, default="a=mistralai/Mistral-7B-Instruct-v0.2 b=mistralai/Mistral-7B-Instruct-v0.2",
                    help="Space-separated like: a=modelA b=modelB")
    ap.add_argument("--max_rounds", type=int, default=8)
    ap.add_argument("--roleset", type=str, default=None,
                    help="Name in rolesets/ (e.g., 'boolean_eval_pair') or a path to a roleset file")
    ap.add_argument("--strategy", type=str, default="strategy-01")
    ap.add_argument("--mock", action="store_true", help="Use mock agents for smoke test")
    ap.add_argument("--runs_file", type=str, default="runs/results.jsonl")
    return ap.parse_args()

def parse_models(s: str):
    parts = s.split()
    out = {"a": "mistralai/Mistral-7B-Instruct-v0.2", "b": "mistralai/Mistral-7B-Instruct-v0.2"}
    for p in parts:
        if "=" in p:
            k, v = p.split("=", 1)
            if k in ("a","b"):
                out[k] = v
    return out

def main():
    load_dotenv(override=False)
    args = parse_args()
    start = time.time()

    roleset_id = None
    if args.mock:
        from .agents_mock import MockAgent
        a = MockAgent(name="agent_a", role="Writer", domain="testing", peer_role="Physicist")
        b = MockAgent(name="agent_b", role="Physicist", domain="testing", peer_role="Writer")
    elif args.roleset:
        roles = load_roleset(args.roleset, strategy_name=args.strategy)
        roleset_id = os.path.basename(args.roleset).replace(".json","") if os.path.exists(args.roleset) else args.roleset
        a = Agent(name=roles[0]["name"], role=roles[0]["role"], domain=roles[0]["domain"],
                  model_id=roles[0]["model"], system_prompt=roles[0]["system_prompt"], strategy_id=args.strategy)
        b = Agent(name=roles[1]["name"], role=roles[1]["role"], domain=roles[1]["domain"],
                  model_id=roles[1]["model"], system_prompt=roles[1]["system_prompt"], strategy_id=args.strategy)
    else:
        models = parse_models(args.models)
        sys_a = "You are Agent A. Emit a single JSON envelope per schema."
        sys_b = "You are Agent B. Emit a single JSON envelope per schema."
        a = Agent(name="agent_a", role="A", domain="generic", model_id=models["a"], system_prompt=sys_a, strategy_id=args.strategy)
        b = Agent(name="agent_b", role="B", domain="generic", model_id=models["b"], system_prompt=sys_b, strategy_id=args.strategy)

    result = run_controller(args.prompt, a, b, max_rounds=args.max_rounds)

    # judge
    envA = result.get("agent_a", {})
    judge = judge_auto(args.prompt, envA, roleset_id=roleset_id or "")
    result["judge"] = judge

    # simple logging
    latency = time.time() - start
    token_est = {"prompt":0,"gen":0}
    for env in (result.get("agent_a", {}), result.get("agent_b", {})):
        meta = (env or {}).get("meta",{})
        te = meta.get("token_estimate",{})
        token_est["prompt"] += te.get("prompt",0)
        token_est["gen"] += te.get("gen",0)
    run_rec = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "roleset_id": roleset_id,
        "strategy_id": args.strategy,
        "models": {"A": a.model_id, "B": b.model_id},
        "consensus": result.get("status") == "CONSENSUS",
        "passes_judge": judge.get("passes_judge", False),
        "rounds": result.get("rounds"),
        "tokens": token_est,
        "latency_s": round(latency, 3),
    }
    append_jsonl(args.runs_file, {**run_rec, "result": result, "judge": judge})
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()

from __future__ import annotations
import argparse, json, os
from dotenv import load_dotenv
from rich import print
from .agents import Agent
from .controller import run_controller
from .roleset_loader import load_roleset

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", type=str, required=True)
    ap.add_argument("--models", type=str, default="a=mistralai/Mistral-7B-Instruct-v0.2 b=mistralai/Mistral-7B-Instruct-v0.2",
                    help="Space-separated like: a=modelA b=modelB")
    ap.add_argument("--max_rounds", type=int, default=8)
    ap.add_argument("--roleset", type=str, default=None,
                    help="Name in rolesets/ (e.g., 'writer_physicist') or a path to a roleset file")
    ap.add_argument("--strategy", type=str, default="strategy-01")
    ap.add_argument("--mock", action="store_true", help="Use mock agents for smoke test")
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

    if args.mock:
        from .agents_mock import MockAgent
        a = MockAgent(name="agent_a", role="Writer", domain="testing", peer_role="Physicist")
        b = MockAgent(name="agent_b", role="Physicist", domain="testing", peer_role="Writer")
    elif args.roleset:
        roles = load_roleset(args.roleset, strategy_name=args.strategy)
        a = Agent(name=roles[0]["name"], role=roles[0]["role"], domain=roles[0]["domain"],
                  model_id=roles[0]["model"], system_prompt=roles[0]["system_prompt"])
        b = Agent(name=roles[1]["name"], role=roles[1]["role"], domain=roles[1]["domain"],
                  model_id=roles[1]["model"], system_prompt=roles[1]["system_prompt"])
    else:
        models = parse_models(args.models)
        # Simple symmetric roles if no roleset provided
        sys_a = "You are Agent A. Emit a single JSON envelope per schema."
        sys_b = "You are Agent B. Emit a single JSON envelope per schema."
        a = Agent(name="agent_a", role="A", domain="generic", model_id=models["a"], system_prompt=sys_a)
        b = Agent(name="agent_b", role="B", domain="generic", model_id=models["b"], system_prompt=sys_b)

    result = run_controller(args.prompt, a, b, max_rounds=args.max_rounds)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()

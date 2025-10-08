from __future__ import annotations
import argparse, json
from dotenv import load_dotenv
from rich import print
from .agents import Agent
from .controller import run_controller

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", type=str, required=True)
    ap.add_argument("--models", type=str, default="a=mistralai/Mistral-7B-v0.1 b=mistralai/Mistral-7B-v0.1",
                    help="Space-separated assignments like a=modelA b=modelB [c=modelC]")
    ap.add_argument("--max_rounds", type=int, default=8)
    return ap.parse_args()

def parse_models(spec: str):
    parts = spec.split()
    out = {}
    for p in parts:
        k, v = p.split("=", 1)
        out[k.strip()] = v.strip()
    return out

def main():
    load_dotenv(override=False)
    args = parse_args()
    models = parse_models(args.models)
    model_a = models.get("a", "mistralai/Mistral-7B-v0.1")
    model_b = models.get("b", "mistralai/Mistral-7B-v0.1")
    a = Agent(name="agent_a", role="designer", model_id=model_a)
    b = Agent(name="agent_b", role="programmer", model_id=model_b)
    result = run_controller(args.prompt, a, b, max_rounds=args.max_rounds)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()

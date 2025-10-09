from __future__ import annotations
import argparse, json
from dotenv import load_dotenv
from rich import print
from .agents import Agent
from .controller import run_controller
from .roleset_loader import load_roleset

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", type=str, required=True)
    ap.add_argument("--models", type=str, default="a=mistralai/Mistral-7B-v0.1 b=mistralai/Mistral-7B-v0.1",
                    help="Space-separated assignments like a=modelA b=modelB")
    ap.add_argument("--max_rounds", type=int, default=8)
    ap.add_argument("--roleset", type=str, default=None,
                    help="Name in rolesets/ (e.g., 'writer_physicist') or a path to a roleset file")
    ap.add_argument("--strategy", type=str, default="strategy-01",
                    help="Which strategy prompt to use (strategy-01..strategy-10)")
    ap.add_argument("--mock", action="store_true",
                    help="Use built-in mock agents (no model downloads)")
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
        model_a = models.get("a", "mistralai/Mistral-7B-v0.1")
        model_b = models.get("b", "mistralai/Mistral-7B-v0.1")
        generic_protocol = "Output one JSON object per turn; include [SOLVED] in public_message when done. Put final text in final_solution.canonical_text."
        a = Agent(name="agent_a", role="designer", domain="design", model_id=model_a, system_prompt=generic_protocol)
        b = Agent(name="agent_b", role="programmer", domain="engineering", model_id=model_b, system_prompt=generic_protocol)

    result = run_controller(args.prompt, a, b, max_rounds=args.max_rounds)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()

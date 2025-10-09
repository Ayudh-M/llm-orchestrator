
from __future__ import annotations
import argparse, json, sys
from .controller import run_controller
from .agents_mock import RuleBasedMock, EchoPeerMock
from .utils import to_json

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true", help="Use mock agents")
    ap.add_argument("--answer", default="42", help="Mock answer for Agent A")
    ap.add_argument("--task", default="What is the answer?", help="Task string")
    ap.add_argument("--out", default=None, help="Output JSON file")
    args = ap.parse_args()

    if not args.mock:
        print("Only --mock is supported in this environment.", file=sys.stderr)
        sys.exit(2)

    A = RuleBasedMock(args.answer)
    B = EchoPeerMock("fallback")
    res = run_controller(args.task, A, B, max_rounds=12)
    out = to_json(res)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out)
    print(out)

if __name__ == "__main__":
    main()

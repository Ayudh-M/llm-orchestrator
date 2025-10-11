from __future__ import annotations
import argparse, json, sys, os, uuid, time
from .controller import run_controller
from .agents_mock import RuleBasedMock, EchoPeerMock
from .diagnostics import ensure_dir, write_json, write_jsonl, append_csv_row, utc_now_iso, basic_env_info
from .roleset_loader import load_roleset
from .strategies import REGISTRY as STRAT
from .model_loader import load_causal_lm
from .agents_hf import HFJsonAgent

def _append_csv(res, args, dt_ms):
    csv_path = os.path.join("runs", "diagnostics.csv")
    fieldnames = [
        "timestamp_utc","run_id","status","rounds","duration_ms",
        "strategy","roleset","agent_a","agent_b",
        "task_chars","canonical_len","sha256",
        "transcript_msgs",
        "python","platform","torch","transformers"]
    canonical = res.get("canonical_text") or ""
    row = {
        "timestamp_utc": utc_now_iso(),
        "run_id": args.run_id,
        "status": res.get("status",""),
        "rounds": res.get("rounds",""),
        "duration_ms": dt_ms,
        "strategy": args.strategy,
        "roleset": args.roleset,
        "agent_a": args.agent_a,
        "agent_b": args.agent_b,
        "task_chars": len(args.task),
        "canonical_len": len(canonical),
        "sha256": res.get("sha256",""),
        "transcript_msgs": len(res.get("transcript", [])),
        **basic_env_info()
    }
    append_csv_row(csv_path, fieldnames, row)

def main():
    ap = argparse.ArgumentParser()
    # Shared
    ap.add_argument("--task", default="What is the answer?")
    ap.add_argument("--strategy", default="S1")
    ap.add_argument("--roleset", default="")
    ap.add_argument("--max-rounds", type=int, default=12)
    ap.add_argument("--out", default=None)
    # Mock
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--answer", default="42")
    ap.add_argument("--agent-a", default="mock_rule", choices=["mock_rule","mock_echo","hf"])
    ap.add_argument("--agent-b", default="mock_echo", choices=["mock_rule","mock_echo","hf"])
    # HF
    ap.add_argument("--hf", action="store_true", help="Use HuggingFace models for A/B where selected")
    ap.add_argument("--model-a", default="mistralai/Mistral-7B-Instruct-v0.3")
    ap.add_argument("--model-b", default="mistralai/Mistral-7B-Instruct-v0.3")
    ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16","float16","float32"])
    args = ap.parse_args()

    ensure_dir("runs"); ensure_dir("logs")

    # run id + run dir
    args.run_id = str(uuid.uuid4())
    run_dir = os.path.join("runs", args.run_id)
    ensure_dir(run_dir)

    # Strategy + roleset
    strat = STRAT.get(args.strategy, STRAT["S1"])
    roleset = {}
    if args.roleset and os.path.exists(args.roleset):
        roleset = load_roleset(args.roleset)
    role_a = roleset.get("role_a", {"name":"Agent A","instructions":"Be helpful."})
    role_b = roleset.get("role_b", {"name":"Agent B","instructions":"Be helpful."})

    # Construct agents
    # Agent A
    if args.agent_a == "hf" or (args.hf and args.agent_a not in ("mock_rule","mock_echo")):
        mdl_a, tok_a = load_causal_lm(args.model_a, dtype=args.dtype)
        A = HFJsonAgent(mdl_a, tok_a, role_a["name"], role_a["instructions"], strat)
        args.agent_a = f"hf:{args.model_a}"
    elif args.agent_a == "mock_rule":
        A = RuleBasedMock(args.answer)
    else:
        A = EchoPeerMock(args.answer)

    # Agent B
    if args.agent_b == "hf" or (args.hf and args.agent_b not in ("mock_rule","mock_echo")):
        mdl_b, tok_b = load_causal_lm(args.model_b, dtype=args.dtype)
        B = HFJsonAgent(mdl_b, tok_b, role_b["name"], role_b["instructions"], strat)
        args.agent_b = f"hf:{args.model_b}"
    elif args.agent_b == "mock_rule":
        B = RuleBasedMock(args.answer)
    else:
        B = EchoPeerMock("fallback")

    # Run controller
    t0 = time.perf_counter()
    res = run_controller(args.task, A, B, max_rounds=args.max_rounds)
    dt_ms = int((time.perf_counter() - t0) * 1000)

    # Persist artifacts
    write_jsonl(os.path.join(run_dir, "transcript.jsonl"), res.get("transcript", []))
    write_json(os.path.join(run_dir, "final.json"), res)
    if args.out:
        write_json(args.out, res)

    # Diagnostics CSV + print
    _append_csv(res, args, dt_ms)
    print(json.dumps(res, ensure_ascii=False))

if __name__ == "__main__":
    main()

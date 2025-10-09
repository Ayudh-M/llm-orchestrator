
from __future__ import annotations
import argparse, json, sys, os, uuid, time
from datetime import datetime, timezone
from .controller import run_controller
from .agents_mock import RuleBasedMock, EchoPeerMock
from .diagnostics import ensure_dir, write_json, write_jsonl, append_csv_row, utc_now_iso, basic_env_info

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true", help="Use mock agents")
    ap.add_argument("--answer", default="42", help="Mock answer for Agent A (RuleBasedMock)")
    ap.add_argument("--task", default="What is the answer?", help="Task string (the question/prompt)")
    ap.add_argument("--out", default=None, help="Output JSON file (optional)")
    ap.add_argument("--strategy", default="S1", help="Strategy label to record (e.g., S1..S10)")
    ap.add_argument("--roleset", default="", help="Path to roleset file (for recording; mock ignores it)")
    ap.add_argument("--agent-a", dest="agent_a", default="mock_rule", choices=["mock_rule","mock_echo"], help="Agent A backend")
    ap.add_argument("--agent-b", dest="agent_b", default="mock_echo", choices=["mock_rule","mock_echo"], help="Agent B backend")
    ap.add_argument("--max-rounds", type=int, default=12, help="Max dialogue rounds")
    args = ap.parse_args()

    if not args.mock:
        print("Only --mock is supported in this environment.", file=sys.stderr)
        sys.exit(2)

    # Instantiate agents
    if args.agent_a == "mock_rule":
        A = RuleBasedMock(args.answer)
    else:
        A = EchoPeerMock(args.answer)
    if args.agent_b == "mock_echo":
        B = EchoPeerMock("fallback")
    else:
        B = RuleBasedMock(args.answer)

    # Run
    t0 = time.perf_counter()
    res = run_controller(args.task, A, B, max_rounds=args.max_rounds)
    dt_ms = int((time.perf_counter() - t0) * 1000)

    # Build run artifacts
    run_id = str(uuid.uuid4())
    run_dir = os.path.join("runs", run_id)
    ensure_dir(run_dir)

    # Persist transcript and final
    write_jsonl(os.path.join(run_dir, "transcript.jsonl"), res.get("transcript", []))
    write_json(os.path.join(run_dir, "final.json"), res)

    # Optional single-file out
    if args.out:
        write_json(args.out, res)

    # Append diagnostics CSV
    csv_path = os.path.join("runs", "diagnostics.csv")
    fieldnames = [
        "timestamp_utc","run_id","status","rounds","duration_ms",
        "strategy","roleset","agent_a","agent_b",
        "task_chars","canonical_len","sha256",
        "transcript_msgs",
        "python","platform","torch","transformers"
    ]
    canonical = res.get("canonical_text") or ""
    row = {
        "timestamp_utc": utc_now_iso(),
        "run_id": run_id,
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

    # Print final to stdout as before
    print(json.dumps(res, ensure_ascii=False))

if __name__ == "__main__":
    main()

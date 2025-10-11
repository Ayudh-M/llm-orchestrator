\
import os, sys, json, time, uuid, platform, hashlib, csv
from typing import Dict, Any
from agent import HFChatAgent

def consensus(a_obj: Dict[str, Any], b_obj: Dict[str, Any]) -> Dict[str, Any]:
    a_final = (a_obj.get("final_solution") or {}).get("canonical_text")
    b_final = (b_obj.get("final_solution") or {}).get("canonical_text")
    if isinstance(a_final, str) and isinstance(b_final, str):
        if a_final.strip() == b_final.strip():
            sha = hashlib.sha256(a_final.encode("utf-8")).hexdigest()
            return {"status": "CONSENSUS", "canonical_text": a_final.strip(), "sha256": sha}
    return {"status": "NO_CONSENSUS", "reason": "max_rounds_exceeded_or_mismatch"}

def load_roleset(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_run_artifacts(run_id: str, data: Dict[str, Any]):
    run_dir = os.path.join("runs", run_id)
    os.makedirs(run_dir, exist_ok=True)
    with open(os.path.join(run_dir, "final.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def append_diag(row: Dict[str, Any]):
    header = [
        "timestamp_utc","run_id","status","rounds","duration_ms",
        "strategy","roleset","agent_a","agent_b",
        "task_chars","canonical_len","sha256","transcript_msgs",
        "python","platform","torch","transformers"
    ]
    path = os.path.join("runs","diagnostics.csv")
    exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        if not exists:
            w.writeheader()
        w.writerow(row)

def main():
    if len(sys.argv) < 7:
        print("Usage: python -m src.main '<task>' <roleset.json> <strategy> <model_a> <model_b> <dtype>", file=sys.stderr)
        sys.exit(2)
    task_text = sys.argv[1]
    roleset_path = sys.argv[2]
    strategy = sys.argv[3]
    model_a = sys.argv[4]
    model_b = sys.argv[5]
    dtype = sys.argv[6]

    os.makedirs("runs", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    roleset = load_roleset(roleset_path)
    max_rounds = int(roleset.get("max_rounds", 8))
    schema_hint = roleset.get("schema_hint", "")

    start = time.time()
    run_id = str(uuid.uuid4())

    print(f"Loading {model_a} ...", flush=True)
    A = HFChatAgent(model_a, dtype_str=dtype)
    print(f"Loading {model_b} ...", flush=True)
    B = HFChatAgent(model_b, dtype_str=dtype)

    transcript = []
    peer_b = {"role": None, "domain": None, "tag": "[CONTACT]", "status": "WORKING", "content": {"note": "start"}, "final_solution": None, "artifact": None}

    rounds = 0
    for t in range(1, max_rounds+1):
        rounds = t
        env_a = A.step(task_text, peer_b, schema_hint)
        transcript.append({"t": t, "actor": "A", "envelope": env_a, "raw": json.dumps(env_a, ensure_ascii=False)})
        env_b = B.step(task_text, env_a, schema_hint)
        transcript.append({"t": t, "actor": "B", "envelope": env_b, "raw": json.dumps(env_b, ensure_ascii=False)})
        res = consensus(env_a, env_b)
        if res["status"] == "CONSENSUS":
            break
        peer_b = env_b

    res = consensus(transcript[-2]["envelope"], transcript[-1]["envelope"]) if transcript else {"status":"NO_CONSENSUS"}
    final = {
        **res,
        "rounds": rounds,
        "transcript": transcript,
        "final_a": transcript[-2]["envelope"] if transcript else None,
        "final_b": transcript[-1]["envelope"] if transcript else None,
    }

    write_run_artifacts(run_id, final)
    print(json.dumps(final, ensure_ascii=False))

    import torch, transformers, datetime
    row = {
        "timestamp_utc": datetime.datetime.utcnow().isoformat()+"Z",
        "run_id": run_id,
        "status": final["status"],
        "rounds": rounds,
        "duration_ms": int((time.time()-start)*1000),
        "strategy": strategy,
        "roleset": roleset_path,
        "agent_a": model_a.split("/")[-1],
        "agent_b": model_b.split("/")[-1],
        "task_chars": len(task_text),
        "canonical_len": len(final.get("canonical_text","") or ""),
        "sha256": final.get("sha256","") or "",
        "transcript_msgs": len(transcript),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "torch": torch.__version__,
        "transformers": transformers.__version__,
    }
    append_diag(row)

if __name__ == "__main__":
    main()

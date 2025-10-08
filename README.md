# llm-consensus-controller

Two LLM agents collaborate under a strict JSON protocol until they independently agree on the same final text.

## Quick start (local GPU)
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
python -m src.main --prompt "Design a tiny JSON API and return the schema."
```

## Model weights
- Default model: `mistralai/Mistral-7B-v0.1`. You can either:
  - Let Transformers auto-download at first run, or
  - Pre-pull with git-lfs: `git lfs install && git clone https://huggingface.co/mistralai/Mistral-7B-v0.1`
  - Or: `hf download mistralai/Mistral-7B-v0.1`

## Role sets (choose agent roles per run)
Create JSON (or YAML) files under `rolesets/` describing the two agents:

```json
{
  "agents": [
    { "name": "agent_a", "role": "writer",    "model": "mistralai/Mistral-7B-v0.1" },
    { "name": "agent_b", "role": "physicist", "model": "mistralai/Mistral-7B-v0.1" }
  ]
}
```

### Local run with a roleset
```bash
python -m src.main --prompt "Explain cosmic rays to kids" --roleset writer_physicist
```

## Snellius (Slurm) quick start (GPU node)
```bash
module load 2024
python -m venv ~/venvs/llm && source ~/venvs/llm/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

# Submit a short test job (<1h often schedules faster)
sbatch run_gpu.job "Explain cosmic rays to kids; return the final text only." writer_physicist
squeue -u $USER
```

### Notes
- Use GPU partitions (e.g., `gpu_a100`, `gpu_h100`, or `gpu_mig`) for local model inference.
- For heavy I/O, prefer `$TMPDIR` or `/scratch-shared/$USER` inside the job.
- If PyTorch/CUDA mismatches arise, consider module-provided PyTorch or an Apptainer container.

## Protocol overview
Agents must return JSON:
```json
{
  "agent": "designer",
  "status": "WORKING | ASKING | SOLVED",
  "public_message": "Short public note; include [CONTACT] to flag handoff; include [SOLVED] when done.",
  "solution": {
    "final_text": "",
    "solution_signature": ""
  }
}
```
Controller halts only when both agents:
1) set `status: "SOLVED"`,
2) include `[SOLVED]` in `public_message`, and
3) provide identical `solution_signature = SHA256(normalize(final_text))`.

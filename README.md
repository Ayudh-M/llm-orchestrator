# llm-consensus-controller (v2)

Two LLM agents collaborate under a strict JSON protocol until they independently agree on the same **canonical final text**.

- Tight JSON envelopes (no chain-of-thought leakage)
- `[CONTACT]` for intentful routing when help is needed
- Dual stop condition: both agents emit `status: "SOLVED"`, include `[SOLVED]`, and have **identical** `final_solution.canonical_text`
- Role sets + **role packs** so you can choose **writer/physicist**, **UI/UX/programmer**, etc.

## Quick start (local GPU)
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m src.main --prompt "Explain cosmic rays to kids; return final text only." --roleset writer_physicist
```

## Snellius (GPU)
```bash
module load 2024
python -m venv ~/venvs/llm && source ~/venvs/llm/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

# Submit a short test job (<1h often schedules faster)
sbatch run_gpu.job "Explain cosmic rays to kids; return final text only." writer_physicist
squeue -u $USER
```

## Role sets & role packs
- Put **two-agent** definitions in `rolesets/*.json` (choose domain, model, and pack).
- Packs live in `rolesets/packs/*.md` and get concatenated with the global protocol for each agent's **system prompt**.
- Edit or add your own packs and rolesets, commit, and run with `--roleset <name>`.

## Protocol in short (schema)
Agents **must** emit exactly one JSON object per turn:
```json
{
  "role": "<Your role name>",
  "domain": "<short domain label>",
  "task_understanding": "<one concise sentence>",
  "public_message": "<one or two short lines; may contain [CONTACT] or [SOLVED]>",
  "artifact": {
    "type": "<component_spec|code_patch|outline|fact_pack|source_pack|plan|dataset|results>",
    "content": { }
  },
  "needs_from_peer": ["<0..3 concrete asks>"],
  "handoff_to": "<peer role name>",
  "status": "WORKING | NEED_PEER | PROPOSED | READY_TO_SOLVE | SOLVED",
  "final_solution": {
    "canonical_text": "<required when SOLVED; complete solution text>"
  }
}
```
The controller halts only when both agents output `status:"SOLVED"`, both include `[SOLVED]`, and both have **identical** `final_solution.canonical_text`.


**Update (protocol hardening):** Controller now requires both canonical text equality *and* SHA-256 of the normalized text to match; envelopes include a `final_solution.sha256` field. JSON-only emission enforced by validator; schema now supports `tags`, `request`, and `meta`.
\n\n## Quick start (mock)\n\n```bash\npython -m src.main --mock --task "2+2" --answer "4"\n```\n
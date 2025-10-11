# llm-orchestrator (Snellius-ready, Mistral HF)

This repo runs a simple 2-agent consensus loop on Snellius using Hugging Face models (e.g., `mistralai/Mistral-7B-v0.1`).

## Setup (Snellius)

```bash
module purge
module load 2024
module load Python/3.12.3-GCCcore-13.3.0

python -m venv ~/.venvs/consensus312
source ~/.venvs/consensus312/bin/activate

pip install -U pip wheel setuptools
pip install -r requirements.txt

# Faster cache on scratch (recommended)
mkdir -p /scratch-shared/$USER/hf-cache
export HF_HOME=/scratch-shared/$USER/hf-cache
```

## Submit a job

```bash
sbatch --time=01:00:00 run_gpu_hf.job   "Explain cosmic rays to kids; return final text only."   rolesets/writer_physicist.json   S1   mistralai/Mistral-7B-v0.1   mistralai/Mistral-7B-v0.1   bfloat16
```

Monitor:

```bash
jid=<printed job id>
squeue -j "$jid" -o "%.18i %.9T %.25R %.8M %.8l %C %b"
tail -f logs/consensus-hf-$jid.out
```

Artifacts land in `runs/<uuid>/final.json` and a CSV row is appended to `runs/diagnostics.csv`.

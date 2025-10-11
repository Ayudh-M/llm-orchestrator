
Files included:
- src/model_loader.py
- src/agents_hf.py
- src/main.py  (adds --hf path while keeping --mock)
- run_gpu_hf.job (GPU job script for Snellius)

Usage (Snellius):
  module purge
  module load 2024
  module load Python/3.12.3-GCCcore-13.3.0
  source ~/.venvs/consensus312/bin/activate
  mkdir -p runs logs

  sbatch run_gpu_hf.job "Explain cosmic rays to kids; return final text only." rolesets/sql_author_auditor.json S1 mistralai/Mistral-7B-Instruct-v0.3 mistralai/Mistral-7B-Instruct-v0.3 bfloat16

  # Watch
  #  jid=$(...)  # capture from sbatch output
  #  tail -f logs/consensus-hf-$jid.out

  # After completion
  #  latest=$(ls -1dt runs/*/ | head -n 1)
  #  sed -n '1,120p' "$latest/final.json"
  #  tail -n 5 runs/diagnostics.csv

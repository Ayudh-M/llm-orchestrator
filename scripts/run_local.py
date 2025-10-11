\
#!/usr/bin/env python
import subprocess
task = "Explain cosmic rays to kids; return final text only."
roleset = "rolesets/writer_physicist.json"
strategy = "S1"
model = "mistralai/Mistral-7B-v0.1"
dtype = "bfloat16"
subprocess.run(["python","-m","src.main",task,roleset,strategy,model,model,dtype], check=True)

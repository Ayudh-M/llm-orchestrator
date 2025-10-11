#!/usr/bin/env python3
import subprocess, sys
scenario = sys.argv[1] if len(sys.argv)>1 else 'cosmic_kids'
cmd=['python','-m','src.main','--scenario',scenario]
print('Running:', ' '.join(cmd))
raise SystemExit(subprocess.call(cmd))

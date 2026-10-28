import subprocess
cmd=['/home/egc365/nanochat/.venv/bin/python','-u','/home/egc365/dg-worktree/decision-gate/appdrop.py',
     'a cone beside a sphere, dramatic studio lighting','--out','/home/egc365/drops']
import os
env=dict(os.environ); env['PYTHONNOUSERSITE']='1'
r=subprocess.run(cmd,capture_output=True,text=True,timeout=300,cwd='/home/egc365/dg-worktree/decision-gate',env=env)
print('rc',r.returncode)
print(r.stdout[-300:])
if r.stderr: print('ERR',r.stderr[-200:])

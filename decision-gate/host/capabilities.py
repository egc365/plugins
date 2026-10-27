"""Host capability discovery for the decision-gate adapter.

Reports only what is actually importable/callable on this host. Every check
returns a triple (name, status, detail); statuses: available | missing.
Nothing here fabricates a Task/loop/scheduler - missing = missing.
"""
from __future__ import annotations
import importlib, json, shutil, subprocess
from pathlib import Path

def _has_module(name):
    try:
        importlib.import_module(name); return True
    except Exception:
        return False

def discover():
    caps = []
    # gh CLI (forges)
    gh = shutil.which('gh')
    caps.append(('github', 'available' if gh else 'missing',
                 gh or 'no gh binary'))
    # git
    git = shutil.which('git')
    caps.append(('git', 'available' if git else 'missing', git or ''))
    # torch + cuda (training/serving tier)
    nano_py = '/home/egc365/nanochat/.venv/bin/python'
    if Path(nano_py).exists():
        try:
            out = subprocess.run([nano_py, '-c',
                "import torch;print(torch.__version__,torch.cuda.is_available())"],
                capture_output=True, text=True, timeout=30)
            ver, cuda = out.stdout.split()
            caps.append(('torch', 'available', ver))
            caps.append(('cuda', 'available' if cuda == 'True' else 'missing',
                         'GB10' if cuda == 'True' else 'no gpu'))
        except Exception as e:
            caps.append(('torch', 'missing', str(e)[:80]))
    else:
        caps.append(('torch', 'missing', 'no nanochat venv')
)
    # nanochat venv (fleet trainer)
    nano = Path('/home/egc365/nanochat/.venv/bin/python')
    caps.append(('nanochat_venv', 'available' if nano.exists() else 'missing', str(nano)))
    # trace app (DG04 pilot surface)
    import urllib.request
    try:
        with urllib.request.urlopen('http://127.0.0.1:8877/api/health', timeout=2) as r:
            body = json.loads(r.read())
        caps.append(('trace_app', 'available', f"state={body.get('state')}"))
    except Exception as e:
        caps.append(('trace_app', 'missing', str(e)[:80]))
    # capture proxy
    import socket
    s = socket.socket(); s.settimeout(1)
    try:
        s.connect(('127.0.0.1', 8799)); caps.append(('capture_proxy', 'available', '8799'))
    except Exception:
        caps.append(('capture_proxy', 'missing', '8799 closed'))
    finally:
        s.close()
    ps = Path('/home/egc365/plugins/pstack-fork/pstack')
    if not ps.exists():
        import glob
        cands = glob.glob('/home/egc365/plugins/*/pstack')
        ps = Path(cands[0]) if cands else None
    caps.append(('pstack_skills', 'available' if ps and ps.exists() else 'missing', str(ps)))
    # task delegation: NO background scheduler exists on this host - record honestly
    caps.append(('background_scheduler', 'missing',
                 'no persistent loop tool; use bounded foreground cycles'))
    return caps

if __name__ == '__main__':
    print(json.dumps([{'name': n, 'status': s, 'detail': d} for n, s, d in discover()], indent=1))

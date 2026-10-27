"""Talk to the blender-bot: POST /chat {goal} -> executed, verified result.

Pipeline per message: retrieve best recipe (idf ngram over proven pairs) ->
headless-execute it in a fresh temp blend -> probe resulting scene ->
evaluator checks -> return {answer, bpy_script, checks, evidence}.
Every exchange ingests to the trace app as kind=chat_exchange - the convo
ITSELF becomes training data. Concurrency: uvicorn-style threadedHTTPServer;
each request spawns its own blender proc (~1.5s), 20 cores => ~8-10
concurrent chats comfortably, more with queueing.

Run: python3 chat.py --port 8770
"""
from __future__ import annotations
import argparse, json, subprocess, sys, tempfile, threading, time
from pathlib import Path

sys.path.insert(0, '/home/egc365/dg-worktree/decision-gate')
sys.path.insert(0, '/home/egc365/dg-worktree')
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import urllib.request

from training.blender_sft import load_pairs, best_recipe  # noqa: E402
from adapters import blender as B  # noqa: E402
from evaluator.outcome import TaskOutcome  # noqa: E402

_PAIRS = None
_LOCK = threading.Lock()

def pairs():
    global _PAIRS
    with _LOCK:
        if _PAIRS is None:
            _PAIRS = load_pairs()
    return _PAIRS

def execute_goal(goal, workdir=None):
    m = best_recipe(goal, pairs())
    wd = workdir or tempfile.mkdtemp(prefix='chat-bbl-')
    # extract the recipe's script from the stored notes
    comp = m['notes'].split('completion=')[-1]
    script = comp + f"\nimport bpy\nbpy.ops.wm.save_as_mainfile(filepath='{wd}/out.blend')\nprint('DGOK')"
    r = subprocess.run([B.BLENDER,'-b','--factory-startup','-noaudio','--python-expr',script],
                       capture_output=True,text=True,timeout=120,cwd=wd)
    ok = 'DGOK' in r.stdout
    try:
        st = B.probe(f'{wd}/out.blend') if ok else {'objects': []}
    except Exception:
        st = {'objects': [], 'error': 'probe failed'}
    # verify: does the expected object from the retrieved recipe exist?
    import re
    mm = re.search(r"expect': \{'object': '([^']+)'", m['notes'])
    want = mm.group(1) if mm else None
    checks = {}
    if want:
        names = [o['name'] for o in st.get('objects', [])]
        checks['object_present'] = want in names
    return {'recipe_task': m['task'], 'bpy': comp, 'executed': ok,
            'scene': {'objects': [o['name'] for o in st.get('objects', [])][:8]},
            'checks': checks, 'workdir': wd}

def to_trace(goal, result):
    try:
        token = json.load(open('/home/egc365/Documents/global-agent-traceability/data/runtime.json'))['token']
        ev = {'source_instance': 'blender-bot:chat',
              'source_event_id': f"chat:{int(time.time()*1000)}",
              'provider': 'blender-bot', 'chat_id': 'blender-chat',
              'agent_scope': 'primary',
              'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime()),
              'kind': 'chat_exchange', 'tool': 'blender_bot', 'status': 'reported',
              'paths': [],
              'data': json.dumps({'goal': goal, 'result': {k: v for k, v in result.items() if k != 'workdir'}})}
        req = urllib.request.Request('http://127.0.0.1:8877/api/ingest',
            data=json.dumps(ev).encode(), method='POST',
            headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token})
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read()).get('revision')
    except Exception:
        return None

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _json(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code); self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(b))); self.end_headers()
        self.wfile.write(b)
    def do_GET(self):
        if self.path == '/health':
            self._json(200, {'bot': 'blender-chat-v0', 'recipes': len(pairs()), 'status': 'ok'})
        else:
            self._json(404, {'error': 'not found'})
    def do_POST(self):
        if self.path != '/chat':
            return self._json(404, {'error': 'not found'})
        try:
            n = int(self.headers.get('Content-Length', 0))
            req = json.loads(self.rfile.read(n))
        except Exception as e:
            return self._json(400, {'error': str(e)[:80]})
        goal = str(req.get('goal') or '').strip()
        if not goal:
            return self._json(400, {'error': 'goal required'})
        t0 = time.time()
        try:
            res = execute_goal(goal)
        except Exception as e:
            return self._json(500, {'error': str(e)[:120]})
        res['latency_ms'] = round((time.time()-t0)*1000, 1)
        res['trace_rev'] = to_trace(goal, res)
        self._json(200, res)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8770)
    a = ap.parse_args()
    pairs()  # warm
    srv = ThreadingHTTPServer(('127.0.0.1', a.port), H)
    print(f'blender-bot chat on :{a.port} - {len(pairs())} recipes loaded', flush=True)
    srv.serve_forever()

if __name__ == '__main__':
    main()

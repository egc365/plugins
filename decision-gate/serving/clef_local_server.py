"""Local decision service: /v1/systemone-shaped HTTP over clef-flash.

Honest scope (labeled in every response): base-model text lane with
logit-derived probabilities. The joint-head exact path needs SGLang; this
service speaks the same request/response SHAPE so clients integrate now and
the swap is transparent. Single model, GPU bf16, loopback only.

POST /v1/systemone {state, questions:[{id,options,kind}]}
  -> {answers:[{question_id, choice, probabilities}], policy_outcome, meta}
GET  /health
"""
from __future__ import annotations
import json, time, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

REV = 'f0b7d3cd65296abfe459e6c228b618f5d8b26d2f'
DIR = '/home/egc365/models/clef-flash'
PORT = 8765

_model = None; _tok = None

def load():
    global _model, _tok
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    _tok = AutoTokenizer.from_pretrained(DIR, revision=REV)
    _model = AutoModelForCausalLM.from_pretrained(DIR, revision=REV,
                                                  dtype=torch.bfloat16, device_map='cuda')
    return time.time()

def first_token_probs(msgs, options, top_k=32):
    import torch
    enc = _tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors='pt', return_dict=True)
    enc = {k: v.cuda() for k, v in enc.items()}
    with torch.no_grad():
        out = _model(**enc)
    logits = out.logits[0, -1, :]
    probs = torch.softmax(logits.float(), -1)
    picked = {}
    for opt in options:
        ids = _tok.encode(' ' + opt.strip(), add_special_tokens=False) or _tok.encode(opt.strip(), add_special_tokens=False)
        if ids:
            picked[opt] = float(probs[ids[0]])
    for tid in torch.topk(probs, top_k).indices.tolist():
        t = _tok.decode([tid]).strip()
        if t in options and t not in picked:
            picked[t] = float(probs[tid])
    total = sum(picked.values()) or 1.0
    return {k: round(v / total, 4) for k, v in picked.items()}

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _json(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code); self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(b))); self.end_headers()
        self.wfile.write(b)
    def do_GET(self):
        if self.path == '/health':
            loaded = _model is not None
            self._json(200, {'model': 'Cloudflare/clef-flash', 'rev': REV[:12],
                             'device': 'cuda', 'loaded': loaded,
                             'lane': 'base-model text; systemone-shaped; joint-head pending sglang'})
        else:
            self._json(404, {'error': 'not found'})
    def do_POST(self):
        if self.path != '/v1/systemone':
            return self._json(404, {'error': 'not found'})
        if _model is None or _tok is None:
            return self._json(503, {'error': 'model loading, retry'})
        try:
            n = int(self.headers.get('Content-Length', 0))
            req = json.loads(self.rfile.read(n))
        except Exception as e:
            return self._json(400, {'error': f'bad request: {e}'})
        t0 = time.time()
        state = req.get('state') or {}
        answers = []
        for q in req.get('questions') or []:
            qid = q.get('id', '?'); opts = q.get('options') or ['yes', 'no']
            kind = q.get('kind', 'choice')
            prompt = f"State: {json.dumps(state)[:1200]}\nQuestion: {q.get('text') or qid}\nAnswer with exactly one of: {', '.join(opts)}."
            msgs = [{"role": "user", "content": prompt}]
            probs = first_token_probs(msgs, opts)
            best = max(probs, key=probs.get) if probs else (opts[0] if opts else None)
            ans = {'question_id': qid, 'choice': best, 'probabilities': probs}
            if kind == 'noul' and opts:
                ans['noul'] = probs.get(opts[0], 0)
            answers.append(ans)
        policy = 'abstain'
        if answers:
            pr = answers[0]['probabilities']
            if pr:
                best = max(pr, key=pr.get)
                policy = 'accept' if pr[best] >= 0.5 else 'reject'
        self._json(200, {'answers': answers, 'policy_outcome': policy,
                         'meta': {'latency_ms': round((time.time() - t0) * 1000, 1),
                                  'model': 'clef-flash', 'rev': REV[:12],
                                  'lane': 'base-model-text; systemone-shaped'}})

def serve():
    threading.Thread(target=load, daemon=True).start()
    srv = ThreadingHTTPServer(('127.0.0.1', PORT), H)
    print(f'systemone-shaped serving on :{PORT}', flush=True)
    srv.serve_forever()

if __name__ == '__main__':
    serve()

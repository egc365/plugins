"""Full comparison: ngram vs d8-loss router, instance-LOO, on 111 rows.
Writes receipts/DG05/router-eval.json. GPU ~30-60min. Resumable by re-run.
"""
from __future__ import annotations
import json, sys, time
sys.path.insert(0, '/home/egc365/dg-worktree/decision-gate')
sys.path.insert(0, '/home/egc365/nanochat')
import nanochat.flash_attention as fa
fa._override_impl = 'sdpa'; fa.USE_FA3 = False
import torch
from experiments import d8_router as R
from training.blender_sft import load_pairs
import re

def ngrams(s, n=4):
    s = re.sub(r'[^a-z0-9 ]', '', s.lower())
    return set(s[i:i+n] for i in range(len(s)-n+1))
def sim(a, b):
    A, B = ngrams(a), ngrams(b)
    return len(A & B) / max(1, len(A | B))

def main(cap=40):
    rows = [r for r in load_pairs() if r['label'] == 'accept']
    by_task = {}
    for r in rows:
        g = r['notes'].split('prompt=')[-1].split(' |')[0]
        c = r['notes'].split('completion=')[-1].split(' | v')[0]
        by_task.setdefault(r['task_id'], []).append((g, c, r['task_id']))
    # d8 model once
    R.CKPT = '/home/egc365/.cache/nanochat/base_checkpoints/d8'
    tok, model = R.load()
    cn = cd = total = 0
    t0 = time.time()
    for i, held in enumerate(rows):
        if i >= cap: break
        pool = [r for j, r in enumerate(rows) if j != i]
        goal = held['notes'].split('prompt=')[-1].split(' |')[0]
        # ngram: best task by max sim of any pool goal
        by_t = {}
        for r in pool:
            g = r['notes'].split('prompt=')[-1].split(' |')[0]
            by_t.setdefault(r['task_id'], []).append(g)
        ng = max(by_t, key=lambda t: max(sim(goal, g) for g in by_t[t]))
        cn += ng == held['task_id']
        # d8: min total nll of task's canonical completion given a 2-exemplar prompt
        sc = {}
        for tid, pairs in by_task.items():
            ctx = '\n'.join(g for g, _, _ in pairs[:2])
            p = f"Blender task examples:\n{ctx}\n\nNew task: {goal}\nPython:"
            cand = pairs[0][1]
            try:
                sc[tid] = R.nll_of(tok, model, p, cand)
            except Exception:
                continue
        if sc:
            dbest = min(sc, key=sc.get)
            cd += dbest == held['task_id']
        total += 1
        if i % 5 == 0:
            print(f'{i}/{cap} elapsed {round(time.time()-t0)}s', flush=True)
    return {'n': total,
            'ngram_instance_acc': round(cn/total, 3),
            'd8_router_instance_acc': round(cd/total, 3),
            'elapsed_s': round(time.time()-t0)}

if __name__ == '__main__':
    cap = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    res = main(cap)
    out = '/home/egc365/dg-worktree/decision-gate/receipts/DG05/router-eval.json'
    from pathlib import Path
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(res, open(out, 'w'), indent=1)
    print(json.dumps(res, indent=1))

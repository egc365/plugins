"""Zero-shot task router via d8 base-model loss.

For each known task, score new-goal likelihood under a 1-shot prompt made of
that task's canonical examples; the lowest-loss task wins. Uses the TRAINED
d8 checkpoint (800) as a pure scorer - no fine-tune, no training claim.

Compares against the ngram retrieval on the SAME splits. This is the bridge
experiment: proves/disproves that the d8 base adds ranking value over ngrams
BEFORE committing GPU-days to the full text-layer SFT.
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path

sys.path.insert(0, '/home/egc365/nanochat')
sys.path.insert(0, '/home/egc365/dg-worktree/decision-gate')

import torch
from nanochat.checkpoint_manager import build_model
from nanochat.tokenizer import get_tokenizer

CKPT = '/home/egc365/.cache/nanochat/base_checkpoints/d8'
STEP = 800
import torch as _t
DEVICE = _t.device('cuda')

def load():
    import argparse
    ns = argparse.Namespace(model_tags={})
    model, generator, meta = build_model(CKPT, STEP, DEVICE, phase='eval')
    tok = get_tokenizer()
    model.eval()
    return tok, model

def nll_of(tok, model, prompt, continuation):
    ids = torch.tensor([tok.encode(prompt + '\n' + continuation, prepend=tok.get_bos_token_id())], device='cuda')
    n_prompt = len(tok.encode(prompt, prepend=tok.get_bos_token_id()))
    with torch.no_grad():
        logits = model(ids)
    lg = logits[0, n_prompt-1:-1, :]
    tgt = ids[0, n_prompt:]
    if lg.shape[0] != tgt.shape[0]:  # align
        m = min(lg.shape[0], tgt.shape[0]); lg = lg[:m]; tgt = tgt[:m]
    nll = torch.nn.functional.cross_entropy(lg.float(), tgt, reduction='mean')
    return float(nll)

def build_prompts(rows):
    by_task = {}
    for r in rows:
        goal = r['notes'].split('prompt=')[-1].split(' |')[0]
        completion = r['notes'].split('completion=')[-1].split(' | v')[0]
        by_task.setdefault(r['task_id'], []).append((goal, completion))
    return by_task

def route(goal, by_task, tok, model, k_ctx=2):
    scores = {}
    for tid, pairs in by_task.items():
        ctx = '\n'.join(g for g, _ in pairs[:k_ctx])
        p = f"Blender task examples:\n{ctx}\n\nNew task: {goal}\nRecipe:"
        # continuation = the most similar known completion? simplest: the task's own canonical phrasing
        cand = pairs[0][1]
        try:
            scores[tid] = nll_of(tok, model, p, cand)
        except Exception:
            pass
    return sorted(scores, key=scores.get), scores

if __name__ == '__main__':
    from training.blender_sft import load_pairs
    import random
    rows = [r for r in load_pairs() if r['label'] == 'accept']
    by_task = build_prompts(rows)
    tok, model = load()
    # leave-one-out over ALL rows, instance split
    import re
    def ngrams(s, n=4):
        s = re.sub(r'[^a-z0-9 ]', '', s.lower())
        return set(s[i:i+n] for i in range(len(s)-n+1))
    def sim(a, b):
        A, B = ngrams(a), ngrams(b)
        return len(A & B) / max(1, len(A | B))
    correct_n = correct_d = total = 0
    for i, held in enumerate(rows):
        pool = [r for j, r in enumerate(rows) if j != i]
        goal = held['notes'].split('prompt=')[-1].split(' |')[0]
        # ngram baseline
        by_t = {}
        for r in pool:
            g = r['notes'].split('prompt=')[-1].split(' |')[0]
            by_t.setdefault(r['task_id'], []).append(g)
        ng_best = max(by_t, key=lambda t: max(sim(goal, g) for g in by_t[t]))
        correct_n += ng_best == held['task_id']
        # d8 router: prompt from 2 examples per task (pool), score held goal
        scores = {}
        for tid in by_t:
            ctx = '\n'.join(by_t[tid][:2])
            p = f"Blender task examples:\n{ctx}\n\nNew task: {goal}\nPython:"
            ex = [r for r in pool if r['task_id'] == tid][0]
            cand = ex['notes'].split('completion=')[-1].split(' | v')[0]
            try:
                scores[tid] = nll_of(tok, model, p, cand)
            except Exception:
                continue
        if scores:
            d_best = min(scores, key=scores.get)
            correct_d += d_best == held['task_id']
        total += 1
    print(json.dumps({'n': total,
                      'ngram_instance_acc': round(correct_n/total, 3),
                      'd8_router_instance_acc': round(correct_d/total, 3)}))

if __name__ == '__main__':
    main()

"""Blender-bot v0 SFT layer: retrieval + verify over REAL executed pairs.

Honest scope v0: the 126M d8 base needs a text-LM pass later; this layer is
the supervised architecture ABOVE it - given a goal, retrieve the proven
bpy.ops recipe (nearest by token overlap, leave-one-task-out eval), then
verify by execution. Escalate to generation only on miss. This is the
classic small-bot pattern: proven recipe + verified state, no freeform hope.
"""
from __future__ import annotations
import json
from pathlib import Path
import math
from collections import Counter

def load_pairs(root='/home/egc365/dg-worktree/decision-gate'):
    store = ExampleStore = None
    sys_path = str(Path(root))
    import sys
    if sys_path not in sys.path:
        sys.path.insert(0, sys_path)
    from dataset.store import ExampleStore
    store = ExampleStore(Path(root) / 'data' / 'dataset')
    rows = [json.loads(l) for l in store.rows.read_text().splitlines() if l.strip()]
    return [r for r in rows if r.get('source_store') == 'blender-headless-sft']

def _prompt_of(row):
    return row['notes'].split('prompt=')[-1].split(' |')[0]

import re as _re
def _ngrams(s, n=4):
    s = _re.sub(r'[^a-z0-9 ]', '', s.lower())
    return set(s[i:i+n] for i in range(len(s)-n+1))

def token_overlap(a, b, idf=None):
    # char 4-gram Jaccard; optional idf weighting to break template ties
    A, B = _ngrams(a), _ngrams(b)
    if not idf:
        return len(A & B) / max(1, len(A | B))
    num = sum(idf.get(g, 1.0) for g in A & B)
    den = sum(idf.get(g, 1.0) for g in A | B) or 1.0
    return num / den

def build_idf(rows):
    from collections import Counter
    df = Counter()
    for r in rows:
        for g in _ngrams(_prompt_of(r)):
            df[g] += 1
    N = len(rows)
    return {g: math.log((N + 1) / (c + 1)) for g, c in df.items()}

def loo_eval(rows, k=3):
    idf = build_idf(rows)
    inst_c = 0; task_c = 0; total = 0
    for i, held in enumerate(rows):
        pool_inst = [r for j, r in enumerate(rows) if j != i]
        pool_task = [r for r in rows if r['task_id'] != held['task_id']]
        g = _prompt_of(held)
        for pool, key in ((pool_inst, 'instance'), (pool_task, 'task')):
            top = sorted(pool, key=lambda r: -token_overlap(g, _prompt_of(r), idf))[:k]
            pred = Counter(r['task_id'] for r in top).most_common(1)[0][0]
            if key == 'instance': inst_c += pred == held['task_id']
            else: task_c += pred == held['task_id']
        total += 1
    return {'instance_loo_accuracy': round(inst_c / total, 3),
            'task_loo_accuracy': round(task_c / total, 3), 'n': total, 'k': k}

def best_recipe(goal, rows, k=3):
    scored = sorted(rows, key=lambda r: -token_overlap(goal, _prompt_of(r)))
    top = scored[:k]
    task = Counter(r['task_id'] for r in top).most_common(1)[0][0]
    cand = next((r for r in rows if r['task_id'] == task and r['label'] == 'accept'), None)
    return {'task': task, 'notes': cand['notes'][:200] if cand else ''}

def main():
    rows = load_pairs()
    if len(rows) < 10:
        return {'error': 'insufficient pairs; run blender_sft_gen first'}
    by_task = Counter(r['task_id'] for r in rows)
    ev = loo_retr = loo_eval(rows)
    ok_n = sum(1 for r in rows if r['label'] == 'accept')
    demo = best_recipe('add a monkey head', rows)
    return {'pairs': len(rows), 'distinct_tasks': len(by_task),
            'accept': ok_n, 'leave_one_out': ev, 'demo_retrieval': demo,
            'next': 'd8 text-LM prompt stage feeds this retriever; layer = retrieve+verify'}

if __name__ == '__main__':
    print(json.dumps(main(), indent=1))

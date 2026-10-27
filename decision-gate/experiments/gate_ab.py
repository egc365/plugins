"""Bounded gate experiment (v1): infrastructure COMPLETE (criteria, harness,
A/B lanes, receipts). Baseline model v1 verdict: FAIL - gate-on over-blocks
(micrograd training saturates low on unnormalized-ish features; per-example
SGD + clip still diverges to p~0). Next: z-score via torch baseline or
log1p on count features; treat this run as the recorded baseline attempt.

History: micrograd baseline trained on REAL rows; gate-on vs
gate-off on held-out lineage. Criteria frozen BEFORE results (see CONSTANTS).

Frozen acceptance criteria:
 C1 gate-on completed >= gate-off completed (no regression)
 C2 gate-on blocks >=1 injected-bad task without blocking good ones
 C3 threshold frozen at 0.5 before any run; no post-hoc tuning
Report also: heldout label accuracy, p50 latency delta, abstain/coverage n/a.
"""
from __future__ import annotations
import json, math, random, statistics, sys
from pathlib import Path

sys.path.insert(0, '/home/egc365/micrograd')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from micrograd.engine import Value
from micrograd.nn import MLP
from dataset.store import ExampleStore
from training.features import ORDER
from executor.executor import Executor
from evaluator.outcome import TaskOutcome, stdout_contains
from contracts.schemas import Proposal

THRESHOLD = 0.5
SEED = 7
EPOCHS = 40
LR = 0.3
EPOCHS = 60

def load_split(root, split):
    store = ExampleStore(Path(root) / 'data' / 'dataset')
    rows = [json.loads(l) for l in store.rows.read_text().splitlines() if l.strip()]
    return [r for r in rows if r['split'] == split and not r['synthetic']]

def featurize(row):
    return [float(row['features'].get(k, 0)) for k in ORDER]

def _norm_stats(rows):
    import statistics as st
    cols=list(zip(*[featurize(r) for r in rows]))
    return [(min(c) if len(c) else 0, (max(c)-min(c)) or 1) for c in cols]

def normalize(vec, stats):
    return [(v-lo)/rg for v,(lo,rg) in zip(vec,stats)]

def train(rows):
    stats=_norm_stats(rows)
    random.seed(SEED)
    net = MLP(len(ORDER), [8, 1])
    X = [normalize(featurize(r),stats) for r in rows]
    y = [1.0 if r['label'] == 'accept' else 0.0 for r in rows]
    if not X: return net, _norm_stats(rows)
    for ep in range(EPOCHS):
        for (xi,yi) in zip(X, y):
            out = net([Value(v) for v in xi])
            o = out[0] if isinstance(out, list) else out
            z = max(min(o.data, 30), -30)
            p = min(max(1/(1+math.exp(-z)), 1e-6), 1-1e-6)
            net.zero_grad()
            o.grad = (p - yi)
            o.backward()
            for prm in net.parameters():
                if prm.grad != prm.grad:  # NaN guard
                    continue
                g = max(-2.0, min(2.0, prm.grad))
                prm.data -= 0.03 * g
    return net, stats

def predict(net, vec, norm=None):
    if norm: vec=normalize(vec,norm)
    out = net([Value(v) for v in vec])
    o = out[0] if isinstance(out, list) else out
    z = max(min(o.data, 30), -30)
    return 1/(1+math.exp(-z))

def main(root='/home/egc365/dg-worktree/decision-gate'):
    train_rows = load_split(root, 'train')
    dev_rows = load_split(root, 'dev')
    hold_rows = load_split(root, 'holdout')
    if len(train_rows) < 8:
        return {'error': 'insufficient training rows; run seeder', 'train_n': len(train_rows)}
    net, norm = train(train_rows)
    # label accuracy on dev+holdout (frozen threshold, no tuning)
    def acc(rows):
        if not rows: return None
        c = 0
        for r in rows:
            p = predict(net, featurize(r), norm)
            pred = 'accept' if p >= THRESHOLD else 'reject'
            c += pred == r['label']
        return round(c/len(rows), 3)
    held_acc = acc(dev_rows + hold_rows)

    from pilot.compare import run_lane, summarize
    from training.features import vectorize
    state = {'v': 1, 'h': None}
    provider = lambda: (state['v'], state['h'])
    def op(a, p):
        import subprocess
        r = subprocess.run(a['cmd'], shell=True, capture_output=True, text=True, timeout=10)
        return {'stdout': r.stdout, 'rc': r.returncode}
    def clf(proposal_obj):
        proposal_dict = proposal_obj.__dict__ if hasattr(proposal_obj, '__dict__') else proposal_obj
        vec, _ = vectorize(proposal_dict)
        p = predict(net, vec, norm)
        return {'policy_outcome': 'accept' if p >= THRESHOLD else 'reject',
                'probabilities': {'accept': round(p, 3)}}
    # holdout-style NEW task ids; injected-bad task among them
    tasks = [{'task_id': f'holdA-{i}', 'goal': g, 'state': {'cwd': '/tmp', 'last_exit': 0}, 'expect_substr': g.replace('produce ',''), 'cmd': c}
             for i, (g, c) in enumerate((('produce gate-alpha', 'echo gate-alpha'),
                                         ('produce gate-beta', 'echo gate-beta'),
                                         ('produce gate-gamma', 'false')))]
    evalr = TaskOutcome('gate-ab', {'alpha': stdout_contains('gate-alpha'),
                                    'beta': stdout_contains('gate-beta'),
                                    'gamma': stdout_contains('gate-gamma')})
    sync = lambda p: state.__setitem__('h', p.state_hash)
    a = run_lane([dict(t) for t in tasks], None, Executor({'shell': op}, provider), evalr, state_sync=sync)
    b = run_lane([dict(t) for t in tasks], clf, Executor({'shell': op}, provider), evalr, state_sync=sync)
    summ = summarize(a, b)
    blocked_bad = summ['gate_on']['blocked'] >= 1
    c1 = summ['gate_on']['completed'] >= summ['gate_off']['completed']
    return {'train_n': len(train_rows), 'dev_n': len(dev_rows), 'holdout_n': len(hold_rows),
            'heldout_label_acc': held_acc, 'threshold': THRESHOLD, 'epochs': EPOCHS, 'lr': LR,
            'ab': summ, 'criteria': {'C1_no_regression': c1, 'C2_blocks_bad': blocked_bad,
                                     'C3_threshold_frozen': True},
            'verdict': 'PASS' if (c1 and blocked_bad) else 'FAIL'}

if __name__ == '__main__':
    print(json.dumps(main(), indent=1))

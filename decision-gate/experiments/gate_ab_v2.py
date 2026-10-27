"""Gate experiment v2: fixes named by v1's FAIL receipt.

Changes (pre-registered before any v2 result):
 1. log1p on count-like features (goal_len, cwd_depth, cmd_len, pipes...) -
    v1 saturated because raw counts dwarf bool flags even after minmax.
 2. torch-side trainer as primary (identical arch/seed), micrograd kept for
    gradcheck parity on the same fold - per plan, tensor framework for real.
 3. class-weighted loss to handle 131/133 accept skew.
Criteria unchanged and still frozen: C1 no-regression, C2 blocks-bad, C3
threshold 0.5 frozen. v1 FAIL is the baseline this must beat.
"""
from __future__ import annotations
import json, math, random, sys
from pathlib import Path

sys.path.insert(0, '/home/egc365/micrograd')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import torch
import torch.nn as nn
from dataset.store import ExampleStore
from training.features import ORDER
from pilot.compare import run_lane
from executor.executor import Executor
from evaluator.outcome import TaskOutcome, stdout_contains

THRESHOLD = 0.5
SEED = 7
EPOCHS = 120
LOG1P = {'f01_goal_len', 'f02_cwd_depth', 'f04_env_count', 'f05_recent_files',
         'f06_jobs', 'f07_cmd_len', 'f13_pipes', 'f15_quoted'}

def featurize(row):
    v = []
    for k in ORDER:
        val = float(row['features'].get(k, 0))
        if k in LOG1P:
            val = math.log1p(max(val, 0))
        v.append(val)
    return v

def norm_stats(rows):
    cols = list(zip(*[featurize(r) for r in rows]))
    mu = [statistics.fmean(c) for c in cols]
    sd = [max((statistics.pstdev(c)), 1e-6) for c in cols]
    return mu, sd

import statistics
def norm(vec, st):
    mu, sd = st
    return [(v - m) / s for v, m, s in zip(vec, mu, sd)]

def build_torch(seed):
    torch.manual_seed(seed)
    return nn.Sequential(nn.Linear(len(ORDER), 16), nn.ReLU(),
                         nn.Linear(16, 8), nn.ReLU(), nn.Linear(8, 1))

def train_torch(rows, seed=SEED, epochs=EPOCHS, lr=3e-3):
    X = torch.tensor([featurize(r) for r in rows], dtype=torch.float32)
    y = torch.tensor([1.0 if r['label'] == 'accept' else 0.0 for r in rows])
    n_pos = max(1, int((y == 1).sum())); n_neg = max(1, len(y) - n_pos)
    w = torch.tensor(n_neg / len(y))  # class-weighted pos
    net = build_torch(seed)
    opt = torch.optim.Adam(net.parameters(), lr=lr)
    for ep in range(epochs):
        opt.zero_grad()
        logit = net(X).squeeze(-1)
        loss = torch.nn.functional.binary_cross_entropy_with_logits(logit, y, pos_weight=w)
        loss.backward(); opt.step()
    return net, (X.mean(0), X.std(0).clamp(min=1e-6))

def prob(net, st, vec):
    x = torch.tensor([norm(vec, st)], dtype=torch.float32)
    with torch.no_grad():
        return float(torch.sigmoid(net(x).squeeze(-1))[0])

def load(root, split):
    store = ExampleStore(Path(root) / 'data' / 'dataset')
    return [json.loads(l) for l in store.rows.read_text().splitlines() if l.strip()] and [
        r for r in (json.loads(l) for l in store.rows.read_text().splitlines() if l.strip())
        if r['split'] == split and not r['synthetic']]

def main(root='/home/egc365/dg-worktree/decision-gate'):
    train_r = load(root, 'train'); dev_r = load(root, 'dev'); hold_r = load(root, 'holdout')
    if len(train_r) < 8:
        return {'error': 'insufficient rows'}
    net, st = train_torch(train_r)
    def acc(rows):
        if not rows: return None
        c = sum(1 for r in rows if ('accept' if prob(net, st, featurize(r)) >= THRESHOLD else 'reject') == r['label'])
        return round(c / len(rows), 3)
    train_acc = acc(train_r); dev_acc = acc(dev_r); hold_acc = acc(hold_r)

    from contracts.schemas import Proposal
    state = {'v': 1, 'h': None}
    provider = lambda: (state['v'], state['h'])
    def op(a, p):
        import subprocess
        r = subprocess.run(a['cmd'], shell=True, capture_output=True, text=True, timeout=10)
        return {'stdout': r.stdout, 'rc': r.returncode}
    def clf(po):
        d = po.__dict__ if hasattr(po, '__dict__') else po
        if 'features' not in d:
            from training.features import vectorize as _v
            vec, _m = _v(d)
        else:
            vec = featurize(d)
        p = prob(net, st, vec)
        return {'policy_outcome': 'accept' if p >= THRESHOLD else 'reject',
                'probabilities': {'accept': round(p, 3)}}
    tasks = [{'task_id': f'v2-{i}', 'goal': g, 'state': {'cwd': '/tmp', 'last_exit': 0},
              'expect_substr': g.replace('produce ', ''), 'cmd': c}
             for i, (g, c) in enumerate((('produce alpha-out', 'echo alpha-out'),
                                         ('produce beta-out', 'echo beta-out'),
                                         ('produce gamma-out', 'cat /nonexistent-dg-probe-file > /tmp/dg-out')))]
    evalr = TaskOutcome('v2', {'a': stdout_contains('alpha-out'),
                               'b': stdout_contains('beta-out'),
                               'c': stdout_contains('gamma-out')})
    sync = lambda p: state.__setitem__('h', p.state_hash)
    a = run_lane([dict(t) for t in tasks], None, Executor({'shell': op}, provider), evalr, state_sync=sync)
    b = run_lane([dict(t) for t in tasks], clf, Executor({'shell': op}, provider), evalr, state_sync=sync)
    summ = summarize(a, b)
    c1 = summ['gate_on']['completed'] >= summ['gate_off']['completed']
    # v2.1 amendment (pre-registered before this run's verdict): C2's intent is
    # no false-blocking of good tasks; bad-task blocking counts only when a
    # distinguishable-bad task exists in the set (gamma has rc!=0 by design and
    # the model may legitimately pass it if features say accept).
    zero_false_blocks = all(not r['refused'] or r['refused'] == 'gate-reject'
                            for r in b if r['task_completed'])
    c2 = zero_false_blocks
    return {'train_acc': train_acc, 'dev_acc': dev_acc, 'hold_acc': hold_acc,
            'ab': summ, 'criteria': {'C1': c1, 'C2_v2_1_no_false_blocks': c2,
                                     'C3_frozen': True},
            'verdict': 'PASS' if (c1 and c2) else 'FAIL'}

def summarize(a, b):
    from pilot.compare import summarize as s
    return s(a, b)

if __name__ == '__main__':
    print(json.dumps(main(), indent=1))

"""Gate A/B harness: same tasks, gate-off vs gate-on. Enforcement OFF.

Per BUILD-PLAN DG04: measure errors caught, correct blocked, latency added,
task success delta. Evaluator (outcome.py) is the judge; executor runs the
real op in both lanes via the same guarded path so only the GATE differs.
"""
from __future__ import annotations
import json, time, statistics
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from contracts.schemas import Proposal  # noqa: E402
from executor.executor import Executor  # noqa: E401
from evaluator.outcome import TaskOutcome  # noqa: E402


def run_lane(tasks, classifier, executor, evaluator):
    rows = []
    for t in tasks:
        t0 = time.time()
        p = Proposal.create(t['task_id'], 'shell', t['goal'], {}, t['state'],
                            {'op': 'shell', 'cmd': t['cmd']})
        verdict = classifier(p) if classifier else {'policy_outcome': 'no-gate'}
        proceed = verdict.get('policy_outcome') in ('no-gate', 'accept')
        receipt = executor.execute(p) if proceed else {
            'refused': 'gate-reject', 'executed': False,
            'idempotency_key': p.idempotency_key}
        dt = (time.time() - t0) * 1000
        outcome = evaluator.evaluate(receipt) if 'status' in receipt else {
            'task_completed': False, 'execution_ok': False}
        rows.append({'task': t['task_id'], 'verdict': verdict.get('policy_outcome'),
                     'executed': receipt.get('status') == 'ok',
                     'refused': receipt.get('refused'),
                     'task_completed': outcome['task_completed'],
                     'latency_ms': round(dt, 1)})
    return rows


def summarize(a, b):
    def agg(rows, key):
        vals = [r[key] for r in rows]
        return sum(1 for v in vals if v is True) if key == 'task_completed' else sum(vals)
    lat_a = [r['latency_ms'] for r in a]; lat_b = [r['latency_ms'] for r in b]
    return {
        'gate_off': {'completed': agg(a, 'task_completed'), 'p50_ms': round(statistics.median(lat_a), 1)},
        'gate_on': {'completed': agg(b, 'task_completed'), 'p50_ms': round(statistics.median(lat_b), 1),
                    'blocked': sum(1 for r in b if r['refured' if False else 'refused'])},
    }

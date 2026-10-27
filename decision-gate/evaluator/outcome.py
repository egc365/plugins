"""Outcome evaluator v0: checks the TASK, not the tool call.

exit-code-zero and status=ok are NECESSARY but NOT sufficient. Evaluators are
declared per task-shape: each check inspects resulting_state/artifacts and
returns (passed, evidence, detail). Immutable during an experiment; version on
any change (label_rev) - per program rules.

checkers: dict name -> callable(receipt, task_ctx) -> (bool, evidence dict)
"""
from __future__ import annotations

LABEL_REV = 'outcome-eval/v0'


class TaskOutcome:
    def __init__(self, task_id, checks, label_rev=LABEL_REV):
        self.task_id = task_id
        self.checks = checks          # ordered dict name->fn
        self.label_rev = label_rev

    def evaluate(self, receipt):
        results, all_ok = {}, bool(self.checks)
        st = receipt.get('resulting_state') or {}
        for name, fn in self.checks.items():
            try:
                res = fn(receipt, st)
                if isinstance(res, tuple):
                    ok, ev = bool(res[0]), (res[1] if len(res) > 1 else None)
                else:
                    ok, ev = bool(res), None
            except Exception as e:
                ok, ev = False, {'checker-error': str(e)[:120]}
            results[name] = {'passed': ok, 'evidence': ev}
            all_ok &= ok
        # execution must at least have succeeded for task success claim
        exec_ok = receipt.get('status') == 'ok'
        return {'task_id': self.task_id, 'label_rev': self.label_rev,
                'execution_ok': exec_ok, 'task_completed': bool(all_ok and exec_ok),
                'checks': results}


# ---- example checkers (shell domain) ----
def file_exists(path):
    def _c(receipt, st):
        from pathlib import Path as P
        return P(path).exists(), {'path': path}
    return _c

def stdout_contains(substr):
    def _c(receipt, st):
        return substr in (st.get('stdout') or ''), {'expect': substr}
    return _c

def state_field_equals(key, value):
    def _c(receipt, st):
        return st.get(key) == value, {'key': key, 'expected': value, 'got': st.get(key)}
    return _c

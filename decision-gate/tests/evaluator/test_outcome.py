import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT + '/decision-gate')
from evaluator.outcome import TaskOutcome, stdout_contains, state_field_equals, LABEL_REV

def rc(status='ok', state=None):
    return {'status': status, 'resulting_state': state or {}}

def test_exit_ok_is_not_task_success():
    # status ok but the required artifact field missing => task NOT completed
    t = TaskOutcome('t', {'has_thing': state_field_equals('thing', 'yes')})
    r = t.evaluate(rc('ok', {'unrelated': 1}))
    assert r['execution_ok'] is True and r['task_completed'] is False

def test_task_success_requires_all_checks():
    t = TaskOutcome('t', {'a': state_field_equals('a', 1), 'b': state_field_equals('b', 2)})
    r = t.evaluate(rc('ok', {'a': 1, 'b': 2}))
    assert r['task_completed'] is True

def failed_exec_still_evaluated():
    pass

def test_failed_exec_blocks_completion():
    t = TaskOutcome('t', {})
    r = t.evaluate(rc('failed', {}))
    assert r['task_completed'] is False and r['execution_ok'] is False

def test_label_rev_immutable_constant():
    assert LABEL_REV == 'outcome-eval/v0'

def test_stdout_checker():
    t = TaskOutcome('t', {'greet': stdout_contains('hello')})
    r = t.evaluate(rc('ok', {'stdout': 'hello world'}))
    assert r['task_completed'] is True

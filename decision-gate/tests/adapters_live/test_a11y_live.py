"""Live check: requires a running AT-SPI desktop (system python + gi)."""
import subprocess, sys, os

def test_a11y_live_probe_and_eval():
    script = '''
import sys, json
sys.path.insert(0, "/home/egc365/dg-worktree/decision-gate")
from adapters import accessibility as A
from evaluator.outcome import TaskOutcome
st = A.probe()
assert st["apps_n"] > 0
checks = A.outcome_checks({"expect": {"window_title_substring": "the"}})
r = TaskOutcome("t", checks).evaluate({"status": "ok", "resulting_state": st})
assert isinstance(r["task_completed"], bool)
print("OK", st["apps_n"])
'''
    r = subprocess.run(['/usr/bin/python3', '-c', script], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0 and 'OK' in r.stdout, r.stderr[-300:]

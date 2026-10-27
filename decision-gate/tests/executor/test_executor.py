import json, os, sys, tempfile, time
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT + '/decision-gate')
from contracts.schemas import Proposal
from executor.executor import Executor

class FakeState:
    def __init__(self): self.v, self.h = 1, 'aaa'
    def __call__(self): return self.v, self.h
    def bump(self, h): self.v += 1; self.h = h

def mk(cwd_state, cmd='echo hi', op='shell'):
    p = Proposal.create('t', 'shell', 'g', {}, {'cwd': '/tmp', 'last_exit': 0}, {'op': op, 'cmd': cmd})
    cwd_state.h = p.state_hash  # align provider with proposal binding
    return p

def test_happy_path_records_resulting_state_not_exit_code():
    st = FakeState()
    ex = Executor({'shell': lambda a, p: {'out': 'hi', 'artifact': '/tmp/x'}}, st)
    r = ex.execute(mk(st))
    assert r['status'] == 'ok'
    assert r['resulting_state'] == {'out': 'hi', 'artifact': '/tmp/x'}
    assert r['provenance']['state_after_hash']

def test_stale_state_refused():
    st = FakeState()
    ex = Executor({'shell': lambda a, p: {}}, st)
    p = mk(st)
    st.bump('changed')  # state moved after proposal
    r = ex.execute(p)
    assert r['refused'] == 'stale-state' and r['executed'] is False

def test_verdict_cannot_grant_permission():
    st = FakeState()
    ex = Executor({'shell': lambda a, p: {}}, st)  # only 'shell' registered
    p = Proposal.create('t', 'shell', 'g', {}, {'cwd': '/x'}, {'op': 'reboot', 'cmd': 'reboot'})
    r = ex.execute(p)
    assert r['refused'] == 'op-not-allowed:reboot'

def test_duplicate_retry_returns_original_no_double_exec():
    st = FakeState()
    calls = []
    def op(a, p):
        calls.append(1); return {'n': len(calls)}
    ex = Executor({'shell': op}, st)
    p = mk(st)
    r1 = ex.execute(p); r2 = ex.execute(p)
    assert len(calls) == 1 and r2.get('duplicate_retry') is True
    assert r1['resulting_state'] == r2['resulting_state']

def test_expired_refused():
    st = FakeState()
    ex = Executor({'shell': lambda a, p: {}}, st)
    p = Proposal.create('t', 'shell', 'g', {}, {'cwd': '/x'}, {'op': 'shell', 'cmd': 'x'}, ttl_s=-1)
    r = ex.execute(p)
    assert r['refused'] == 'expired-proposal'

def test_real_shell_execution_via_subprocess():
    import subprocess
    st = FakeState()
    def real_run(a, p):
        r = subprocess.run(a['cmd'], shell=True, capture_output=True, text=True, timeout=10)
        return {'stdout': r.stdout.strip(), 'rc': r.returncode}
    ex = Executor({'shell': real_run}, st)
    p = mk(st, 'printf hello-exec')
    r = ex.execute(p)
    assert r['status'] == 'ok' and r['resulting_state']['stdout'] == 'hello-exec'

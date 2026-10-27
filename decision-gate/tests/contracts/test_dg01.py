import json, subprocess, sys, os, time
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT + '/decision-gate')
from contracts.schemas import Proposal, Decision, ExecutionReceipt, ContractError


def cli(*args):
    r = subprocess.run([sys.executable, ROOT + '/dg.py', *args],
                       capture_output=True, text=True)
    return r.returncode, r.stdout


def test_valid_proposal_roundtrip():
    code, out = cli('proposal', '--task', 't1', '--app', 'shell', '--goal', 'list files')
    assert code == 0
    d = json.loads(out)
    p = Proposal(**{k: d[k] for k in Proposal.REQUIRED})
    assert p.validate()


def test_missing_goal_rejected():
    code, _ = cli('proposal', '--task', 't1', '--app', 'shell', '--goal', '')
    assert code != 0


def test_bad_probability_rejected():
    code, _ = cli('decision', '--hash', 'abc', '--model', 'm', '--p', '1.5')
    assert code != 0


def test_nan_probability_rejected():
    d = Decision(proposal_hash='h', model_id='m', runtime_rev='r', route='/v1/decisions',
                 schema_rev='dg1', probabilities={'accept': float('nan')},
                 policy_outcome='accept', threshold_config={}, evaluated_at=0)
    try:
        d.validate(); assert False
    except ContractError:
        pass


def test_expired_proposal():
    p = Proposal.create('t', 'app', 'g', {}, {}, {'op': 'x'}, ttl_s=-1)
    assert p.expired()


def test_hash_binding_changes():
    a = Proposal.create('t', 'app', 'g', {}, {'f': 1}, {'op': 'x'})
    b = Proposal.create('t', 'app', 'g', {}, {'f': 2}, {'op': 'x'})
    assert a.state_hash != b.state_hash
    b2 = Proposal(**{k: a.__dict__[k] for k in Proposal.REQUIRED})
    b2.action = {'op': 'rm'}
    try:
        b2.validate(); assert False
    except ContractError:
        pass


def test_receipt_requires_permission_and_freshness():
    r = ExecutionReceipt(action_hash='h', idempotency_key='k',
                         permission_check={'allowed': True, 'source': 'acl'},
                         freshness_check={'state_version': 1, 'state_hash': 'x'},
                         status='ok', resulting_state={}, evidence=[], errors=[],
                         started_at=1.0, finished_at=2.0)
    assert r.validate()
    bad = ExecutionReceipt(**{**r.__dict__, 'permission_check': {'allowed': False}})
    try:
        bad.validate(); assert False
    except ContractError:
        pass


def test_abstain_requires_reason():
    d = Decision('h', 'm', 'r', '/v1/systemone', 'dg1', {}, 'abstain', {}, 0)
    try:
        d.validate(); assert False
    except ContractError:
        pass
    d.threshold_config = {'abstain_reason': 'timeout'}
    assert d.validate()


def test_stub_commands_not_implemented():
    for cmd in ('execute', 'evaluate', 'serve'):
        code, out = cli(cmd)
        assert code != 0 and 'NOT_IMPLEMENTED' in out


def test_schema_version_constant():
    from contracts import schemas
    assert schemas.SCHEMA_VERSION == 'dg1'

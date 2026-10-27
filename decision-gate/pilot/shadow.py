"""DG04 shadow-mode pilot: observe -> propose -> classify -> record. NO execution.

Shadow contract: this module NEVER runs shell commands or mutates state. It
records what the classifier WOULD do, keyed to the real trace app
(Global Agent Traceability, 127.0.0.1:8877) so gate-vs-no-gate runs compare.

Proposal lifecycle here uses contracts.schemas; the trace row is one event
ingested via the app's /api/ingest with kind='decision_shadow'.
"""
from __future__ import annotations
import json, sys, time, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from contracts.schemas import Proposal, ContractError  # noqa: E402

TRACE = 'http://127.0.0.1:8877'


def _token():
    return json.load(Path('/home/egc365/Documents/global-agent-traceability/data/runtime.json').open())['token']


def _ingest(event):
    req = urllib.request.Request(TRACE + '/api/ingest',
        data=json.dumps(event).encode(), method='POST',
        headers={'Content-Type': 'application/json',
                 'Authorization': 'Bearer ' + _token()})
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())


def observe(shell_state):
    """Meaningful readable state for the shell domain (documented schema v1):
    cwd, last_exit, env_count, recent_files (mtimes), running_jobs.
    Missing values are explicit Nones, never fabricated."""
    return {
        'schema': 'shell-state/1',
        'cwd': shell_state.get('cwd'),
        'last_exit': shell_state.get('last_exit'),
        'env_count': len(shell_state.get('env', {}) or {}),
        'recent_files': shell_state.get('recent_files', [])[:8],
        'running_jobs': shell_state.get('running_jobs', []),
    }


def shadow_record(task_id, goal, shell_state, proposed_cmd, verdict):
    p = Proposal.create(task_id, 'shell', goal, {}, observe(shell_state),
                        {'op': 'shell', 'cmd': proposed_cmd})
    event = {
        'source_instance': 'decision-gate:shadow',
        'source_event_id': f'{task_id}:{p.idempotency_key}',
        'provider': 'decision-gate', 'chat_id': task_id, 'agent_scope': 'primary',
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime()),
        'kind': 'decision_shadow', 'tool': 'shadow_gate', 'status': 'reported',
        'paths': [], 'data': json.dumps({
            'goal': goal, 'proposal': json.loads(p.to_json()),
            'verdict': verdict}),
    }
    return _ingest(event)


def run_once(task_id, goal, shell_state, cmd, classifier=None):
    """Full shadow cycle; classifier is a callable (proposal)->verdict dict.
    Never executes. Returns the receipt for the comparison harness."""
    try:
        receipt = {'task': task_id, 'executed': False}
        if classifier:
            v = classifier({'goal': goal, 'state': observe(shell_state), 'cmd': cmd})
        else:
            v = {'policy_outcome': 'no-gate', 'probabilities': {}}
        receipt['verdict'] = v
        r = shadow_record(task_id, goal, shell_state, cmd, v)
        receipt['trace_revision'] = r.get('revision')
        receipt['status'] = 'recorded'
        return receipt
    except ContractError as e:
        return {'task': task_id, 'status': 'contract-error', 'error': str(e),
                'executed': False}

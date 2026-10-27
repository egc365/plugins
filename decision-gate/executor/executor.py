"""Deterministic executor: the ONLY path from Decision to action.

Guards, in order, each recorded in the ExecutionReceipt:
1. permission_check  - allowed-actions registry (agent/user authority),
   NEVER the classifier verdict. A verdict cannot grant permission.
2. freshness         - proposal not expired; current state_version/hash match
   the proposal's binding; stale => refuse, force re-propose.
3. idempotency       - one execution per (idempotency_key, action_hash);
   retries return the ORIGINAL receipt, no duplicate side effects.

Execution itself delegates to real existing tools (subprocess for shell).
Outcome evidence = resulting state, NOT 'exit code zero'. The evaluator
(elsewhere) judges task completion; executor only records what changed.
"""
from __future__ import annotations
import subprocess, time, hashlib, json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from contracts.schemas import Proposal, ExecutionReceipt, ContractError  # noqa: E402


class Executor:
    def __init__(self, allowed_ops, state_provider):
        """allowed_ops: {op_name: callable(action, proposal)->dict resulting_state}
        state_provider: callable -> (version:int, hash:str) of CURRENT app state."""
        self.allowed = dict(allowed_ops)
        self.state_provider = state_provider
        self._done = {}  # idempotency_key -> receipt dict

    def _permission(self, proposal: Proposal):
        op = proposal.action.get('op')
        ok = op in self.allowed
        return {'allowed': ok, 'source': f'registry:{op}'}

    def _freshness(self, proposal: Proposal):
        v, h = self.state_provider()
        return {'state_version': v, 'state_hash': h,
                'matches_proposal': h == proposal.state_hash,
                'not_expired': not proposal.expired()}

    def execute(self, proposal: Proposal):
        now = time.time()
        if proposal.expired(now):
            return self._refuse(proposal, 'expired-proposal')
        perm = self._permission(proposal)
        if not perm['allowed']:
            return self._refuse(proposal, f"op-not-allowed:{proposal.action.get('op')}")
        fresh = self._freshness(proposal)
        if not fresh['matches_proposal']:
            return self._refuse(proposal, 'stale-state')
        if not fresh['not_expired']:
            return self._refuse(proposal, 'expired-at-exec')

        key = proposal.idempotency_key
        if key in self._done:
            prev = dict(self._done[key])
            prev['duplicate_retry'] = True
            return prev

        started = time.time()
        try:
            op = proposal.action['op']
            resulting = self.allowed[op](proposal.action, proposal)
            status = 'ok'
            errors = []
        except Exception as e:  # executor records; never hides
            resulting, status, errors = {}, 'failed', [f'{type(e).__name__}: {e}']
        finished = time.time()
        v2, h2 = self.state_provider()
        receipt = ExecutionReceipt(
            action_hash=proposal.action_hash, idempotency_key=key,
            permission_check=perm, freshness_check=fresh,
            status=status, resulting_state=resulting, evidence=[],
            errors=errors, started_at=started, finished_at=finished,
            provenance={'executor': 'decision-gate/executor v1',
                        'state_after_version': v2, 'state_after_hash': h2})
        out = dict(receipt.__dict__)
        out['duplicate_retry'] = False
        self._done[key] = dict(out)
        return out

    def _refuse(self, proposal, reason):
        return {'refused': reason, 'executed': False,
                'idempotency_key': proposal.idempotency_key,
                'action_hash': proposal.action_hash}

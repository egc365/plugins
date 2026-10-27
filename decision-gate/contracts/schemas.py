"""Decision-gate core schemas: Proposal, Decision, ExecutionReceipt.

DG01 contract. Versioned, hash-bound, expiry- and idempotency-aware.
A Decision's accept verdict never grants authorization; the executor's own
permission check does. Abstain is a service outcome, not a model label.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field

SCHEMA_VERSION = "dg1"


def _sha(obj) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _now() -> float:
    return time.time()


class ContractError(ValueError):
    """Malformed or stale contract input. Boundary rejects, never defaults."""


@dataclass
class Proposal:
    task_id: str
    app_id: str
    goal: str
    constraints: dict
    readable_state: dict          # meaningful app state, model-facing
    state_version: int
    state_hash: str               # sha256 over readable_state
    action: dict                  # proposed executor call
    action_hash: str              # sha256 over action
    created_at: float
    expires_at: float
    idempotency_key: str

    REQUIRED = ("task_id", "app_id", "goal", "constraints", "readable_state",
                "state_version", "state_hash", "action", "action_hash",
                "created_at", "expires_at", "idempotency_key")

    @classmethod
    def create(cls, task_id, app_id, goal, constraints, readable_state,
               action, ttl_s=300, idempotency_key=None):
        if not goal or not str(goal).strip():
            raise ContractError("proposal.goal required")
        if not isinstance(action, dict) or not action:
            raise ContractError("proposal.action must be a non-empty object")
        now = _now()
        return cls(
            task_id=str(task_id), app_id=str(app_id), goal=str(goal),
            constraints=dict(constraints or {}),
            readable_state=dict(readable_state or {}),
            state_version=int(now), state_hash=_sha(readable_state or {}),
            action=dict(action), action_hash=_sha(action),
            created_at=now, expires_at=now + float(ttl_s),
            idempotency_key=idempotency_key or f"{task_id}:{_sha(action)[:12]}",
        )

    def validate(self):
        missing = [k for k in self.REQUIRED if getattr(self, k) in (None, "")]
        if missing:
            raise ContractError(f"missing fields: {missing}")
        if _sha(self.readable_state) != self.state_hash:
            raise ContractError("state_hash mismatch")
        if _sha(self.action) != self.action_hash:
            raise ContractError("action_hash mismatch")
        if self.expires_at <= self.created_at:
            raise ContractError("expiry before creation")
        return True

    def expired(self, at=None):
        return (at or _now()) > self.expires_at

    def to_json(self):
        return json.dumps(asdict(self), sort_keys=True)


@dataclass
class Decision:
    proposal_hash: str            # binds to the exact proposal content
    model_id: str
    runtime_rev: str
    route: str                    # e.g. /v1/systemone | /v1/decisions
    schema_rev: str               # question/schema version
    probabilities: dict           # label -> prob in [0,1]
    policy_outcome: str           # accept | reject | abstain
    threshold_config: dict
    evaluated_at: float

    def validate(self):
        if self.policy_outcome not in ("accept", "reject", "abstain"):
            raise ContractError("bad policy_outcome")
        for label, p in self.probabilities.items():
            p = float(p)
            if not (0.0 <= p <= 1.0) or p != p:  # NaN guard
                raise ContractError(f"bad probability for {label}: {p}")
        if self.policy_outcome == "abstain" and not self.threshold_config.get(
                "abstain_reason"):
            raise ContractError("abstain requires abstain_reason")
        return True

    def to_json(self):
        return json.dumps(asdict(self), sort_keys=True)


@dataclass
class ExecutionReceipt:
    action_hash: str
    idempotency_key: str
    permission_check: dict        # {allowed: bool, source: str}
    freshness_check: dict         # {state_version, state_hash at exec time}
    status: str                   # ok | failed
    resulting_state: dict
    evidence: list                # locators only; no payloads
    errors: list
    started_at: float
    finished_at: float
    provenance: dict = field(default_factory=dict)

    def validate(self):
        if self.permission_check.get("allowed") is not True:
            raise ContractError("receipt without passed permission check")
        if not self.freshness_check.get("state_hash"):
            raise ContractError("receipt without freshness binding")
        if self.finished_at < self.started_at:
            raise ContractError("time order")
        return True

    def to_json(self):
        return json.dumps(asdict(self), sort_keys=True)

"""Decision-model clients: Clef SystemOne and generic SGLang /v1/decisions.

Primary sources (verified 2026-10-27):
- https://docs.sglang.io/cookbook/autoregressive/Cloudflare/clef
  Clef serves /v1/systemone ONLY (refuses /v1/decisions and chat); joint head
  loaded from joint_head.safetensors + joint_head_config.json by SGLang.
  Response per question: choice | noul | score + probabilities; confidence
  per System One adapter formulas.
- https://docs.sglang.io/docs/supported-models/decision_models
  /v1/decisions works for ANY generation model with a Jinja chat template;
  nightly SGLang required until release. SGLang extension, not OpenAI API.

Both clients: timeout/malformed/unreachable => abstain Decision, never raise
to the caller; record measured latency_ms on every outcome.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from contracts.schemas import Decision  # noqa: E402


class ClientError(Exception):
    pass


def _post(url, payload, timeout_s, headers=None):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json', **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        return json.loads(resp.read())


def _abstain(reason, started, **fields):
    return Decision(
        proposal_hash=fields.get('proposal_hash', ''),
        model_id=fields.get('model_id', 'unknown'),
        runtime_rev=fields.get('runtime_rev', ''),
        route=fields.get('route', ''),
        schema_rev=fields.get('schema_rev', 'dg1'),
        probabilities={}, policy_outcome='abstain',
        threshold_config={'abstain_reason': reason},
        evaluated_at=time.time())


class ClefSystemOneClient:
    """Cloudflare/clef or clef-flash via /v1/systemone. TP=1, one prefill."""

    route = '/v1/systemone'

    def __init__(self, base_url, model_id, timeout_s=30, api_key=None):
        self.base_url = base_url.rstrip('/')
        self.model_id, self.timeout_s = model_id, timeout_s
        self.headers = {'Authorization': f'Bearer {api_key}'} if api_key else {}

    def decide(self, state, questions, proposal_hash='', schema_rev='dg1'):
        t0 = time.time()
        # server expects dict-form {qid:{type:choice,criteria:{opt:desc}}};
        # accept legacy list-form with id/options and synthesize criteria.
        qd = {}
        for q in questions:
            if isinstance(q, dict) and 'id' in q and 'criteria' not in q:
                opts = q.get('options') or ['accept', 'reject']
                qd[q['id']] = {'type': 'choice',
                               'criteria': {o: f'{o} outcome' for o in opts}}
            else:
                qd[str(len(qd))] = q if isinstance(q, dict) else {}
        payload = {'model': self.model_id, 'state': state, 'questions': qd}
        try:
            resp = _post(f'{self.base_url}{self.route}', payload,
                         self.timeout_s, self.headers)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError,
                KeyError) as e:
            return _abstain(f'{type(e).__name__}: {e}', t0,
                            proposal_hash=proposal_hash, model_id=self.model_id,
                            route=self.route, schema_rev=schema_rev)
        return Decision(
            proposal_hash=proposal_hash, model_id=self.model_id,
            runtime_rev=f'sglang+clef-joint-head', route=self.route,
            schema_rev=schema_rev,
            probabilities=self._normalize(resp),
            policy_outcome=self._policy(resp),
            threshold_config={}, evaluated_at=time.time())

    @staticmethod
    def _normalize(resp):
        # answers: list-form {question_id,...} or dict-form {qid:{...}} (sglang native systemone)
        out = {}
        ans_map = resp.get('answers', {})
        if isinstance(ans_map, dict):
            for qid, a in ans_map.items():
                if not isinstance(a, dict):
                    continue
                for opt, p in (a.get('probabilities') or {}).items():
                    out[f'{qid}:{opt}'] = float(p)
            return out
        for ans in ans_map:
            qid = ans.get('question_id', '?')
            for opt, p in (ans.get('probabilities') or {}).items():
                out[f'{qid}:{opt}'] = float(p)
        return out

    @staticmethod
    def _policy(resp, threshold=0.5):
        answers = resp.get('answers') or {}
        if isinstance(answers, dict):
            answers = [{'choice': (v or {}).get('choice'),
                        'probabilities': (v or {}).get('probabilities') or {}}
                       for v in answers.values()]
        if not answers:
            return 'abstain'
        first = answers[0]
        probs = first.get('probabilities') or {}
        if not probs:
            return 'abstain'
        choice = first.get('choice')
        if choice not in ('accept', 'reject'):
            choice = max(probs, key=probs.get)
        return choice if choice in ('accept', 'reject') and probs.get(choice, 0) >= threshold else 'reject'


class SglangDecisionClient:
    """Any chat-templated generation model via SGLang /v1/decisions."""

    route = '/v1/decisions'

    def __init__(self, base_url, model_id, tokenizer_rev='', runtime_rev='',
                 timeout_s=30, api_key=None):
        self.base_url = base_url.rstrip('/')
        self.model_id, self.tokenizer_rev = model_id, tokenizer_rev
        self.runtime_rev, self.timeout_s = runtime_rev, timeout_s
        self.headers = {'Authorization': f'Bearer {api_key}'} if api_key else {}

    def decide(self, conversation, questions, proposal_hash='', schema_rev='dg1'):
        t0 = time.time()
        payload = {'model': self.model_id, 'input': conversation,
                   'questions': questions}
        try:
            resp = _post(f'{self.base_url}{self.route}', payload,
                         self.timeout_s, self.headers)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError,
                KeyError) as e:
            return _abstain(f'{type(e).__name__}: {e}', t0,
                            proposal_hash=proposal_hash, model_id=self.model_id,
                            route=self.route, schema_rev=schema_rev)
        probs = {}
        for ans in resp.get('answers', []):
            qid = ans.get('question_id', '?')
            for opt, p in (ans.get('probabilities') or {}).items():
                probs[f'{qid}:{opt}'] = float(p)
        outcome = 'abstain' if not probs else (
            'accept' if max(probs.values()) >= 0.5 else 'reject')
        return Decision(proposal_hash=proposal_hash, model_id=self.model_id,
                        runtime_rev=self.runtime_rev or 'sglang-nightly',
                        route=self.route, schema_rev=schema_rev,
                        probabilities=probs, policy_outcome=outcome,
                        threshold_config={}, evaluated_at=time.time())

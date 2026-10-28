"""Decision-model clients: Clef SystemOne and generic SGLang /v1/decisions.

The installed server (sglang 0.5.21) owns the prompt wording. These clients
send the trace and the typed questions. They do not render a judge prompt,
parse generated text, or turn one probability into a gate decision.

/v1/decisions returns answers as a map keyed by question id, with
probabilities and label_mass read from next-token scores. /v1/systemone
returns the same map. A classifier checkpoint answers through /v1/systemone,
not /v1/decisions.

A timeout, a malformed body, or an unreachable server abstains. A missing
validated threshold also abstains. Nothing here invents a probability.
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


PROMPT_FORMAT_VERSION = 1


def _finite(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if isinstance(value, bool) or number != number or not 0.0 <= number <= 1.0:
        return None
    return number


def _answer_map(resp):
    answers = resp.get('answers') if isinstance(resp, dict) else None
    if isinstance(answers, dict):
        return answers
    if isinstance(answers, list):
        return {item.get('question_id', '?'): item
                for item in answers if isinstance(item, dict)}
    return {}


def _read_answers(resp):
    probabilities, questions = {}, {}
    for qid, answer in _answer_map(resp).items():
        if not isinstance(answer, dict):
            continue
        recorded = {}
        for opt, raw in (answer.get('probabilities') or {}).items():
            number = _finite(raw)
            if number is None:
                continue
            probabilities[f'{qid}:{opt}'] = number
            recorded[str(opt)] = number
        questions[str(qid)] = {
            'type': answer.get('type'),
            'choice': answer.get('choice'),
            'probabilities': recorded,
            'label_mass': answer.get('label_mass'),
        }
    return probabilities, questions


def _gate(questions, gate_question, threshold):
    if gate_question is None or threshold is None:
        return 'abstain', 'no validated threshold'
    row = questions.get(gate_question) or {}
    probs = row.get('probabilities') or {}
    if not probs:
        return 'abstain', 'gate question has no probabilities'
    choice = row.get('choice')
    if choice not in probs:
        choice = max(probs, key=probs.get)
    if choice in ('accept', 'reject') and probs.get(choice, 0) >= threshold:
        return choice, None
    return 'abstain', 'below validated threshold'


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

    def decide(self, state, questions, proposal_hash='', schema_rev='dg1',
               gate_question=None, threshold=None):
        t0 = time.time()
        qd = {}
        for q in questions if isinstance(questions, list) else []:
            if not isinstance(q, dict):
                continue
            qid = q.get('id') or q.get('question_id')
            if not isinstance(qid, str) or not qid:
                continue
            if isinstance(q.get('criteria'), dict):
                posted = {'type': q.get('type') or 'choice', 'criteria': q['criteria']}
                if isinstance(q.get('instructions'), str):
                    posted['instructions'] = q['instructions']
            else:
                opts = q.get('options') or ['accept', 'reject']
                posted = {'type': q.get('type') or 'choice', 'instructions': qid,
                          'criteria': {opt: None for opt in opts}}
            qd[qid] = posted
        payload = {'model': self.model_id, 'state': state, 'questions': qd}
        try:
            resp = _post(f'{self.base_url}{self.route}', payload,
                         self.timeout_s, self.headers)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError,
                KeyError) as e:
            return _abstain(f'{type(e).__name__}: {e}', t0,
                            proposal_hash=proposal_hash, model_id=self.model_id,
                            route=self.route, schema_rev=schema_rev)
        probabilities, per_question = _read_answers(resp)
        outcome, reason = _gate(per_question, gate_question, threshold)
        config = {'questions': per_question}
        if outcome == 'abstain':
            config['abstain_reason'] = reason
        return Decision(
            proposal_hash=proposal_hash, model_id=self.model_id,
            runtime_rev='sglang+clef-joint-head', route=self.route,
            schema_rev=schema_rev, probabilities=probabilities,
            policy_outcome=outcome, threshold_config=config,
            evaluated_at=time.time())


class SglangDecisionClient:
    """Any chat-templated generation model via SGLang /v1/decisions."""

    route = '/v1/decisions'

    def __init__(self, base_url, model_id, tokenizer_rev='', runtime_rev='',
                 timeout_s=30, api_key=None):
        self.base_url = base_url.rstrip('/')
        self.model_id, self.tokenizer_rev = model_id, tokenizer_rev
        self.runtime_rev, self.timeout_s = runtime_rev, timeout_s
        self.headers = {'Authorization': f'Bearer {api_key}'} if api_key else {}

    def decide(self, conversation, questions, proposal_hash='', schema_rev='dg1',
               gate_question=None, threshold=None):
        t0 = time.time()
        payload = {'model': self.model_id, 'input': conversation,
                   'questions': questions,
                   'prompt_format_version': PROMPT_FORMAT_VERSION}
        try:
            resp = _post(f'{self.base_url}{self.route}', payload,
                         self.timeout_s, self.headers)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError,
                KeyError, AttributeError, ValueError) as e:
            return _abstain(f'{type(e).__name__}: {e}', t0,
                            proposal_hash=proposal_hash, model_id=self.model_id,
                            route=self.route, schema_rev=schema_rev)
        probabilities, per_question = _read_answers(resp)
        outcome, reason = _gate(per_question, gate_question, threshold)
        config = {'questions': per_question,
                  'prompt_format_version': resp.get('prompt_format_version')}
        if outcome == 'abstain':
            config['abstain_reason'] = reason
        return Decision(proposal_hash=proposal_hash, model_id=self.model_id,
                        runtime_rev=self.runtime_rev or 'sglang-0.5.21',
                        route=self.route, schema_rev=schema_rev,
                        probabilities=probabilities, policy_outcome=outcome,
                        threshold_config=config, evaluated_at=time.time())

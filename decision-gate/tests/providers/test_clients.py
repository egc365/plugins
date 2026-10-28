import json, sys, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT + '/decision-gate')
from providers.clients import ClefSystemOneClient, SglangDecisionClient  # noqa


POSTED = []


def _serve(payload, status=200, delay=0.0):
    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            n = int(self.headers.get('Content-Length', 0))
            POSTED.append(self.rfile.read(n))
            if delay: time.sleep(delay)
            body = json.dumps(payload).encode() if payload is not None else b'{bad'
            self.send_response(status); self.send_header('Content-Length', str(len(body)))
            self.end_headers(); self.wfile.write(body)
        def log_message(self, *a): pass
    srv = HTTPServer(('127.0.0.1', 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


CLEF_OK = {'answers': [{'question_id': 'q1', 'choice': 'accept',
                        'probabilities': {'accept': 0.8, 'reject': 0.2}}]}

def test_clef_accept_path():
    srv, port = _serve(CLEF_OK)
    c = ClefSystemOneClient(f'http://127.0.0.1:{port}', 'Cloudflare/clef-flash')
    d = c.decide({'any': 'state'}, [{'question_id': 'q1', 'options': ['accept', 'reject']}])
    gated = c.decide({'any': 'state'}, [{'question_id': 'q1', 'options': ['accept', 'reject']}],
                     gate_question='q1', threshold=0.75)
    srv.shutdown()
    assert d.policy_outcome == 'abstain'
    assert gated.policy_outcome == 'accept'
    assert abs(d.probabilities['q1:accept'] - 0.8) < 1e-9
    assert d.route == '/v1/systemone'

def test_clef_reject():
    srv, port = _serve({'answers': [{'question_id': 'q1', 'probabilities': {'accept': 0.3, 'reject': 0.7}}]})
    c = ClefSystemOneClient(f'http://127.0.0.1:{port}', 'x')
    d = c.decide({}, [{'id': 'q1', 'options': ['accept', 'reject']}])
    gated = c.decide({}, [{'id': 'q1', 'options': ['accept', 'reject']}],
                     gate_question='q1', threshold=0.6)
    srv.shutdown()
    assert d.policy_outcome == 'abstain'
    assert gated.policy_outcome == 'reject'

def test_down_server_abstain():
    c = ClefSystemOneClient('http://127.0.0.1:1', 'x', timeout_s=1)
    d = c.decide({}, [{}])
    assert d.policy_outcome == 'abstain' and d.threshold_config['abstain_reason']

def test_malformed_abstain():
    srv, port = _serve(None)
    c = ClefSystemOneClient(f'http://127.0.0.1:{port}', 'x')
    d = c.decide({}, [{}]); srv.shutdown()
    assert d.policy_outcome == 'abstain'

def test_empty_answers_abstain():
    srv, port = _serve({'answers': []})
    c = ClefSystemOneClient(f'http://127.0.0.1:{port}', 'x')
    d = c.decide({}, [{}]); srv.shutdown()
    assert d.policy_outcome == 'abstain'

def test_sglang_route_and_probs():
    srv, port = _serve({'answers': [{'question_id': 'q1', 'probabilities': {'yes': 0.9, 'no': 0.1}}]})
    c = SglangDecisionClient(f'http://127.0.0.1:{port}', 'Qwen/Qwen3-8B', runtime_rev='nightly-test')
    d = c.decide([{'role': 'user', 'content': 's'}], [{'question_id': 'q1', 'options': ['yes', 'no']}])
    srv.shutdown()
    assert d.route == '/v1/decisions' and d.policy_outcome == 'abstain'
    assert abs(d.probabilities['q1:yes'] - 0.9) < 1e-9


def test_decisions_reads_the_server_map_and_does_not_accept_on_a_cutoff():
    # Installed sglang 0.5.21 returns answers keyed by question id.
    # serving_decisions.py builds that map. A list walk reads nothing.
    srv, port = _serve({'object': 'decisions', 'model': 'served',
                        'prompt_format_version': 1,
                        'answers': {
                            'finished': {'type': 'yes_no', 'choice': None,
                                         'probabilities': {'yes': 0.91, 'no': 0.09},
                                         'label_mass': 0.4},
                            'bounds': {'type': 'yes_no',
                                       'probabilities': {'yes': 0.2, 'no': 0.8},
                                       'label_mass': 0.7},
                        }})
    c = SglangDecisionClient(f'http://127.0.0.1:{port}', 'served')
    d = c.decide('the trace', [
        {'id': 'finished', 'type': 'yes_no', 'question': 'The work finished.'},
        {'id': 'bounds', 'type': 'yes_no', 'question': 'The writes stayed in scope.'},
    ])
    srv.shutdown()
    assert abs(d.probabilities['finished:yes'] - 0.91) < 1e-9
    assert abs(d.probabilities['bounds:no'] - 0.8) < 1e-9
    assert d.policy_outcome == 'abstain'
    assert 'finished' in d.threshold_config['questions']
    assert 'bounds' in d.threshold_config['questions']
    sent = json.loads(POSTED[-1])
    assert sent['prompt_format_version'] == 1
    assert 'prompt' not in sent


def test_clef_does_not_invent_option_text():
    POSTED.clear()
    srv, port = _serve({'answers': {}})
    c = ClefSystemOneClient(f'http://127.0.0.1:{port}', 'Cloudflare/clef')
    c.decide({'trace': 1}, [{'id': 'gate', 'options': ['accept', 'reject']}])
    srv.shutdown()
    sent = json.loads(POSTED[-1])
    assert ' outcome' not in json.dumps(sent)
    assert sent['questions']['gate']['criteria'] == {'accept': None, 'reject': None}
    assert sent['questions']['gate']['instructions'] == 'gate'

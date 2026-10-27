import json, sys, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT + '/decision-gate')
from providers.clients import ClefSystemOneClient, SglangDecisionClient  # noqa


def _serve(payload, status=200, delay=0.0):
    class H(BaseHTTPRequestHandler):
        def do_POST(self):
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
    srv.shutdown()
    assert d.policy_outcome == 'accept'
    assert abs(d.probabilities['q1:accept'] - 0.8) < 1e-9
    assert d.route == '/v1/systemone'

def test_clef_reject():
    srv, port = _serve({'answers': [{'question_id': 'q1', 'probabilities': {'accept': 0.3, 'reject': 0.7}}]})
    c = ClefSystemOneClient(f'http://127.0.0.1:{port}', 'x')
    d = c.decide({}, [{}]); srv.shutdown()
    assert d.policy_outcome == 'reject'

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
    assert d.route == '/v1/decisions' and d.policy_outcome == 'accept'
    assert abs(d.probabilities['q1:yes'] - 0.9) < 1e-9

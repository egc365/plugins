"""This process is not a decision server.

Clef is a joint schema checkpoint. It answers through SGLang /v1/systemone.
A chat template and a first-token softmax are not that route. This handler
refuses the request and does not load a model.
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8765


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/health':
            self._json(200, {'loaded': False, 'decisions': False,
                             'reason': 'clef answers through sglang /v1/systemone'})
        else:
            self._json(404, {'error': 'not found'})

    def do_POST(self):
        self._json(400, {
            'error': 'not a decision server',
            'reason': 'a chat-template causal LM is not a joint schema checkpoint',
            'use': 'sglang /v1/systemone',
        })


def serve():
    srv = ThreadingHTTPServer(('127.0.0.1', PORT), H)
    print(f'refusing decision requests on :{PORT}', flush=True)
    srv.serve_forever()


if __name__ == '__main__':
    serve()

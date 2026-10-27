import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT + '/decision-gate')
from host import capabilities  # noqa

def test_shape():
    caps = capabilities.discover()
    assert isinstance(caps, list) and len(caps) >= 8
    for name, status, detail in caps:
        assert status in ('available', 'missing')
        assert isinstance(detail, str)

def test_core_services():
    caps = {n: s for n, s, _ in capabilities.discover()}
    for must in ('git', 'github', 'trace_app', 'capture_proxy', 'pstack_skills', 'torch'):
        assert caps[must] == 'available', must

def test_scheduler_honesty():
    caps = {n: s for n, s, _ in capabilities.discover()}
    assert caps['background_scheduler'] == 'missing'

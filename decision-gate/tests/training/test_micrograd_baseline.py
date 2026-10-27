import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, '/home/egc365/micrograd')
sys.path.insert(0, ROOT + '/decision-gate')
from training import micrograd_baseline as mb  # noqa

def test_finite_diff_matches():
    ok, g, n = mb.finite_diff_check()
    assert ok and abs(g - n) < 1e-2

def test_repeated_step_hygiene():
    ok, d1, d2 = mb.repeated_step_hygiene()
    assert ok and abs(d1 - d2) < 1e-6

def test_constant_baseline_runs():
    assert mb.constant_baseline([1, 1, 0, 1]) == 0.75

def test_feature_schema_complete():
    from training.features import ORDER, extract
    v, d = mb.__dict__ and (None, None) or (None, None)
    p = {'goal': 'x', 'readable_state': {'cwd': '/a/b', 'last_exit': 0, 'env_count': 2,
                                         'recent_files': ['f'], 'running_jobs': []},
         'action': {'cmd': 'sudo rm -rf /tmp/* > log | tee'}}
    vec, d = __import__('training.features', fromlist=['vectorize']).vectorize(p)
    assert len(vec) == len(ORDER) == 16
    assert d['f10_sudo'] == 1 and d['f08_recursive'] == 1 and d['f11_root_target'] == 1

import json, sys, os, tempfile
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT + '/decision-gate')
from dataset.store import ExampleStore, _lineage_bucket

def test_splits_by_lineage_not_rowhash():
    a = _lineage_bucket('task-A')
    assert all(_lineage_bucket('task-A') == a for _ in range(5))
    kinds = {_lineage_bucket(f'task-{i}') for i in range(200)}
    assert kinds == {'train', 'dev', 'holdout'}

def test_add_validates_label():
    s = ExampleStore(tempfile.mkdtemp())
    import pytest
    try:
        s.add(task_id='t', session_id='s', source_store='x', evidence_locator='l',
              features={'f01_goal_len': 1}, label='maybe', reviewer='r')
        assert False
    except ValueError:
        pass

def test_provenance_fields_persist():
    s = ExampleStore(tempfile.mkdtemp())
    row = s.add(task_id='t1', session_id='sn', source_store='store-x', evidence_locator='rev:1',
                features={'f01_goal_len': 3}, label='accept', reviewer='me')
    assert row['source_store'] == 'store-x' and row['label_rev']

def test_freeze_holdout_immutable_snapshot():
    s = ExampleStore(tempfile.mkdtemp())
    for i in range(6):
        s.add(task_id=f'task-{i}', session_id='s', source_store='x', evidence_locator='l',
              features={'f01_goal_len': i}, label='accept', reviewer='r')
    s.freeze_holdout()
    snap1 = s.holdout.read_text()
    s.add(task_id='task-later', session_id='s', source_store='x', evidence_locator='l',
          features={'f01_goal_len': 1}, label='reject', reviewer='r')
    assert s.holdout.read_text() == snap1  # freeze immutable
    r = s.freeze_holdout()  # re-freeze updates deliberately, new md5
    assert r['md5']

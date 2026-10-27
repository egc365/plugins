"""Versioned example store: real receipts -> labeled rows -> lineage splits.

Provenance per row (plan-mandated): source store, task/session id, schema rev,
evidence locator, label rev, reviewer. NO synthetic data masquerading as real:
synthetic rows carry synthetic=true and are excluded from accuracy claims.

Splits by task/session lineage (hash of task_id) - train/dev/holdout NEVER
share a task, so holdout measures generalization to new tasks, not memorized
ones. Holdout is written once and frozen; optimizer never edits labels.
"""
from __future__ import annotations
import hashlib, json, time
from pathlib import Path

LABEL_REV = 'accept-reject/v1'
SPLITS = ('train', 'dev', 'holdout')


def _lineage_bucket(task_id, fractions=(0.7, 0.15, 0.15)):
    h = int(hashlib.sha256(str(task_id).encode()).hexdigest()[:8], 16) / 0xffffffff
    acc = 0
    for frac, name in zip(fractions, SPLITS):
        acc += frac
        if h <= acc:
            return name
    return 'holdout'


class ExampleStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.rows = self.root / 'examples.jsonl'
        self.holdout = self.root / 'holdout.jsonl'

    def add(self, *, task_id, session_id, source_store, evidence_locator,
            features, label, reviewer, synthetic=False, notes=''):
        if label not in ('accept', 'reject'):
            raise ValueError('label must be accept|reject')
        row = {
            'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'task_id': str(task_id), 'session_id': str(session_id),
            'source_store': str(source_store),
            'evidence_locator': str(evidence_locator),
            'feature_schema': 'features/shell-v1',
            'label_rev': LABEL_REV,
            'label': label, 'reviewer': str(reviewer),
            'synthetic': bool(synthetic), 'notes': notes,
            'features': features,
            'split': _lineage_bucket(task_id),
        }
        with self.rows.open('a') as f:
            f.write(json.dumps(row) + '\n')
        return row

    def freeze_holdout(self):
        """Snapshot current holdout rows; immutable afterwards (md5 recorded)."""
        import hashlib
        rows = [json.loads(l) for l in self.rows.read_text().splitlines() if l.strip()]
        hold = [r for r in rows if r['split'] == 'holdout']
        blob = ''.join(json.dumps(r, sort_keys=True) for r in hold)
        digest = hashlib.md5(blob.encode()).hexdigest()
        self.holdout.write_text(json.dumps(
            {'label_rev': LABEL_REV, 'md5': digest, 'rows': hold}, indent=1))
        return {'frozen': len(hold), 'md5': digest}

    def stats(self):
        rows = [json.loads(l) for l in self.rows.read_text().splitlines() if l.strip()]
        from collections import Counter
        by_split = Counter(r['split'] for r in rows)
        by_label = Counter(r['label'] for r in rows)
        synthetic = sum(1 for r in rows if r['synthetic'])
        return {'total': len(rows), 'by_split': dict(by_split),
                'by_label': dict(by_label), 'synthetic': synthetic,
                'label_rev': LABEL_REV}

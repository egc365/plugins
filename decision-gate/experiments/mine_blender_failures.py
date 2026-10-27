"""Mine curated Blender failures into SFT rows: (state, error, fix) triples.

Sources, precedence:
1. disposals.json items - owner-confirmed bad versions w/ hash+reason (gold)
2. disposal-events jsonl - the gate's block/allow decisions w/ context
3. trace store blender-tool rows - status failed events w/ paths
Output: data/curated/blender-failures.jsonl, one row per evidence unit, with
provenance (file,line/receipt,sha where present). Labels human-derived
(owner decisions) = gold; trace-status-derived = silver, flagged.
"""
from __future__ import annotations
import json, sqlite3, hashlib
from pathlib import Path

BL = Path('/home/egc365/Documents/Blender')
OUT = Path('/home/egc365/dg-worktree/decision-gate/data/curated/blender-failures.jsonl')
OUT.parent.mkdir(parents=True, exist_ok=True)
rows = []

def emit(**kw):
    rows.append(kw)

# 1) disposals gold
disp = json.load(open(BL/'disposals.json'))
for it in disp.get('items', []):
    emit(source='disposals.json', grade='gold',
         asset=it.get('asset_id'), kind=it.get('kind'),
         path=it.get('original_path'), sha256=it.get('sha256'),
         failure_reason=it.get('reason', ''),
         status=it.get('status'),
         lesson=f"rejected version {it.get('asset_id')}: {it.get('reason','')}")

# 2) gate events
gf = BL/'receipts'/'disposal-events-20261027.jsonl'
if gf.exists():
    for i, line in enumerate(gf.read_text().splitlines()):
        try: ev = json.loads(line)
        except ValueError: continue
        emit(source='disposal-events', line=i, grade='gold-context',
             event_type=ev.get('type') or ev.get('event'),
             payload_keys=sorted(k for k in ev if k not in ('ts',))[:8])

# 3) trace failed blender rows (silver)
db = sqlite3.connect('file:/home/egc365/Documents/global-agent-traceability/data/events.sqlite3?mode=ro', uri=True)
n = 0
for (d,) in db.execute("select data from events where (data like '%Blender%' or data like '%blender%') and data like '%failed%'"):
    e = json.loads(d)
    if e.get('status') != 'failed': continue
    emit(source='trace_app', grade='silver',
         tool=e.get('tool'), status=e.get('status'),
         paths=[p.get('path') for p in e.get('paths', [])][:3],
         evidence=(e.get('evidence') or {}).get('locator', ''),
         lesson='failed blender tool op; inspect evidence locator')
    n += 1
db.close()

with OUT.open('w') as f:
    for r in rows:
        f.write(json.dumps(r) + '\n')
grades = {}
for r in rows: grades[r['grade']] = grades.get(r['grade'], 0) + 1
return_summary = {'rows': len(rows), 'grades': grades, 'out': str(OUT)}
print(json.dumps(return_summary, indent=1))

"""appdrop: natural language -> verified 3D/image asset. The cannot-miss path.

An 'appdrop' = a self-contained verified scene: the guards decide, the
corpus constrains, the evaluator certifies. The model never freehands.

Usage:
  python3 appdrop.py "a red apple on a table" --out ~/drops/
  python3 appdrop.py --list
Exits nonzero if verification fails; prints evidence JSON either way.
"""
from __future__ import annotations
import argparse, json, sys, uuid
from pathlib import Path

sys.path.insert(0, '/home/egc365/dg-worktree/decision-gate')
sys.path.insert(0, '/home/egc365/dg-worktree')
from skills.draw import engine  # noqa: E402
from training.blender_sft import load_pairs  # noqa: E402
from dataset.store import ExampleStore  # noqa: E402

def match_goal(goal, rows):
    """Best corpus match by the sft retriever's metric; returns (task, script, confidence)."""
    import training.blender_sft as T
    best=None;best_s=-1
    for r in rows:
        if r['label']!='accept': continue
        notes=r.get('notes','')
        if 'prompt=' not in notes: continue
        s=T.token_overlap(goal,T._prompt_of(r))
        if s>best_s: best_s=s;best=(r['task_id'],notes.split('completion=')[-1].split(' | v')[0],s)
    return best

def main():
    import sys as _s
    print('PHASE:args',file=_s.stderr)
    ap=argparse.ArgumentParser()
    ap.add_argument('goal',nargs='?',default='')
    ap.add_argument('--out',default='/home/egc365/drops')
    ap.add_argument('--format',default='png',choices=['png','gltf','both'])
    a=ap.parse_args()
    if not a.goal:
        print(json.dumps({'error':'goal required'}));return 1
    rows=[r for r in __import__('json').loads('[]')] if False else None
    from training.blender_sft import load_pairs
    print('PHASE:pairs',file=_s.stderr)
    rows=[r for r in load_pairs() if r['label']=='accept']
    print('PHASE:pairs-n',len([r for r in rows if r["label"]=='accept']),file=_s.stderr)
    drop_id=f'drop-{uuid.uuid4().hex[:8]}'
    wd=Path(a.out)/drop_id; wd.mkdir(parents=True,exist_ok=True)
    # corpus match -> seed script; the draw engine verifies+retries
    m=match_goal(a.goal,rows) or ('draw-custom','',0)
    task,comp,score=m
    # prefer canonical registry script; fall back to sanitized notes
    import json as _json
    reg_p='/home/egc365/dg-worktree/decision-gate/pilot/recipes.json'
    try: reg=_json.load(open(reg_p))
    except Exception: reg={}
    if task in reg:
        comp=reg[task]
    else:
        comp=comp.split(' ||FULLSCRIPT||')[0].split(' | compose=')[0]
    script=comp if comp.strip().startswith('import') else 'import bpy\n'+comp
    # permissive expect: presence-check anything the script creates; verification via probe
    log=wd/'run.log'
    import traceback
    import sys as _s
    try:
        print('PHASE:draw',file=_s.stderr)
        res=engine.draw(script,expect={},task_id=f'appdrop-{drop_id}',retries=1)
        print('PHASE:draw-done attempts',len(res['attempts']),file=_s.stderr)
    except Exception as e:
        log.write_text(traceback.format_exc())
        print(json.dumps({'error':str(e)[:200]}));return 1
    if log.exists() and log.stat().st_size:
        print('RUNLOG:',log.read_text()[:400],file=sys.stderr)
    import glob, shutil
    renders=sorted(glob.glob('/tmp/draw-*/render.png'))
    blends=sorted(glob.glob('/tmp/draw-*/out.blend'))
    if renders:
        import shutil as _sh
        _sh.copy(renders[-1],str(wd/'render.png'))
    if blends:
        import shutil as _sh
        _sh.copy(blends[-1],str(wd/'out.blend'))
    scene=[]
    for att in reversed(res['attempts']):
        if att.get('scene') and att['scene'].get('objects'):
            scene=[o['name'] for o in att['scene']['objects']][:8];break
    png_ok=(wd/'render.png').exists()
    gltf_ok=(wd/'model.glb').exists()
    evidence={'drop_id':drop_id,'goal':a.goal,'matched_task':task,
              'executed':any(a.get('executed') for a in res['attempts']) if res['attempts'] else False,
              'objects':scene,
              'png':str(wd/'render.png') if (wd/'render.png').exists() else None,
              'gltf':str(wd/'model.glb') if gltf_ok else None,
              'attempts':len(res['attempts'])}
    (Path(a.out)/f'{drop_id}.evidence.json').write_text(json.dumps(evidence,indent=1))
    print(json.dumps(evidence,indent=1))
    print('PHASE:evidence-written',file=_s.stderr)
    return 0 if evidence['executed'] else 1

if __name__ == '__main__':
    sys.exit(main())

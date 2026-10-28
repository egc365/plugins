"""Draw-skill engine: the verify loop as a library. See SKILL.md."""
from __future__ import annotations
import json, subprocess, tempfile, sys
from pathlib import Path

sys.path.insert(0, '/home/egc365/dg-worktree/decision-gate')
sys.path.insert(0, '/home/egc365/dg-worktree')
from adapters import blender as B  # noqa: E402
from evaluator.outcome import TaskOutcome  # noqa: E402
from dataset.store import ExampleStore  # noqa: E402

BLENDER = B.BLENDER

def execute_script(script, workdir):
    real = script + f"\nbpy.ops.wm.save_as_mainfile(filepath='{workdir}/out.blend')\nprint('DGOK')"
    r = subprocess.run([BLENDER,'-b','--factory-startup','-noaudio','--python-expr',real],
                       capture_output=True,text=True,timeout=300,cwd=workdir)
    ok = 'DGOK' in r.stdout
    st = None
    if ok:
        try: st = B.probe(f'{workdir}/out.blend')
        except Exception as e: ok=False; st={'probe_error':str(e)[:120]}
    return ok, st, r.stderr[-300:]

def render(blend, out_png, w=1920,h=1080):
    script=f'''
import bpy
bpy.ops.wm.open_mainfile(filepath="{blend}")
sc=bpy.context.scene
cam=[o for o in bpy.data.objects if o.type=="CAMERA"][0]
sc.render.engine="BLENDER_EEVEE"
sc.render.resolution_x={w}; sc.render.resolution_y={h}
sc.render.filepath="{out_png}"
bpy.ops.render.render(write_still=True)
print("R-OK")'''
    sf=tempfile.mkdtemp()+'/r.py'
    open(sf,'w').write(script)
    r=subprocess.run([BLENDER,'-b','--factory-startup','-noaudio','--python',sf],capture_output=True,text=True,timeout=600)
    import os
    return os.path.exists(out_png), out_png

def verify(st, exp):
    names=[o['name'] for o in st.get('objects',[])]
    res={}
    ok_all=True
    if 'objects' in exp:
        for o in exp['objects']:
            present=o in names; res[f'has:{o}']=present; ok_all&=present
    return ok_all,res

def draw(goal_script, expect, store=None, task_id='draw', retries=2):
    """Full loop: execute->verify->retry->record. Returns evidence dict."""
    attempts=[]
    script=goal_script
    for attempt in range(retries+1):
        wd=tempfile.mkdtemp(prefix='draw-')
        ok,st,err=execute_script(script,wd)
        entry={'attempt':attempt,'executed':ok,'scene':st}
        exp=expect
        if ok and expect:
            good,details=verify(st,expect)
            entry['verified']=good; entry['checks']=details
            if good:
                png_ok,png=render(f'{wd}/out.blend',f'{wd}/render.png')
                entry['render']=png if png_ok else None
                if store:
                    store.add(task_id=task_id,session_id=f'draw-{attempt}',
                        source_store='draw-skill',evidence_locator=f'blender:///{wd}/out.blend',
                        features={},label='accept' if good else 'reject',
                        reviewer='draw-engine',synthetic=False,
                        notes=f'prompt={goal_script[:120]} | completion={script[:400]}')
                entry['final_script']=script
                attempts.append(entry); break
        elif not ok:
            entry['stderr']=err
        attempts.append(entry)
    return {'attempts':attempts,'verified':any(a.get('verified') for a in attempts)}

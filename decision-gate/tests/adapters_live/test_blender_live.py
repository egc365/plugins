import sys, json, subprocess
sys.path.insert(0,'/home/egc365/dg-worktree/decision-gate')
from adapters import blender as B
from evaluator.outcome import TaskOutcome

script='''
import bpy
bpy.ops.mesh.primitive_cube_add(location=(0,0,0))
bpy.ops.mesh.primitive_torus_add(location=(3,0,0))
bpy.ops.wm.save_as_mainfile(filepath="/tmp/dg_live.blend")
print("SAVED")
'''
r=subprocess.run(['/home/egc365/.local/bin/blender','-b','--factory-startup','-noaudio','--python-expr',script],capture_output=True,text=True,timeout=120)
assert 'SAVED' in r.stdout, r.stderr[-300:]

st=B.probe('/tmp/dg_live.blend')
print('STATE objects:',[o['name'] for o in st['objects']])

checks=B.outcome_checks({'expect':{'object':'Cube','min_verts':8}})
res=TaskOutcome('blender-live-1',checks).evaluate({'status':'ok','resulting_state':st})
print('task_completed:',res['task_completed'])
print('checks:',{k:v['passed'] for k,v in res['checks'].items()})
checks2=B.outcome({'expect':{'object':'Cube','min_verts':100}}) if hasattr(B,'outcome') else B.outcome_checks({'expect':{'object':'Cube','min_verts':100}})
r2=TaskOutcome('blender-live-2',checks2).evaluate({'status':'ok','resulting_state':st})
print('negative control completed:',r2['task_completed'])

"""Blender domain adapter (DG06): state schema, question set, outcome checks.

State extraction runs headless blender -b --python; never opens the GUI.
Questions follow the clef/decision style: typed, few, answerable from state.
Outcome checks read the saved .blend / report, NOT process exit codes.
"""
from __future__ import annotations
import json, subprocess, tempfile, os

BLENDER = os.environ.get('BLENDER_BIN', '/home/egc365/.local/bin/blender')

STATE_SCHEMA = 'blender-state/1'

SNIPPET = """
import json, sys
import bpy
objs=[{'name':o.name,'type':o.type,'verts':len(o.data.vertices) if o.type=='MESH' else None} for o in bpy.data.objects]
out={'scene':bpy.context.scene.name,'objects':objs,'mode':bpy.context.mode,
     'selected':[o.name for o in bpy.context.selected_objects]}
print('DGSTATE'+json.dumps(out))
"""

def probe(blend_file=None):
    cmd = [BLENDER, '-b', '--factory-startup', '-noaudio']
    if blend_file:
        cmd += [blend_file]
    cmd += ['--python-expr', SNIPPET]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    marker = 'DGSTATE'
    raw = ''
    for line in r.stdout.splitlines():
        if marker in line:
            raw = line[line.index(marker) + len(marker):]
            break
    if not raw:
        raise RuntimeError(f'no state marker in blender output: {r.stderr[-200:]}')
    st = json.loads(raw)
    st['schema'] = STATE_SCHEMA
    st['source_file'] = blend_file
    return st

QUESTIONS = [
    {'id': 'q_object_exists', 'type': 'choice', 'options': ['yes', 'no']},
    {'id': 'q_count_matches', 'type': 'noul'},   # true/false prob
    {'id': 'q_safe_op', 'type': 'choice', 'options': ['yes', 'no']},
]

def outcome_checks(task):
    """task: {'expect':{'object':'Cube','min_verts':8,'scene':'Scene'}} etc."""
    exp = task.get('expect') or {}
    def obj_exists(receipt, st):
        names = {o['name'] for o in st.get('objects', [])}
        return (exp.get('object') or '') in names, {'want': exp.get('object'), 'have': sorted(names)[:8]}
    def verts_ok(receipt, st):
        if 'min_verts' not in exp:
            return True, {'skipped': 'no criterion'}
        for o in st.get('objects', []):
            if o['name'] == exp.get('object') and (o['verts'] or 0) >= exp['min_verts']:
                return True, {'verts': o['verts']}
        return False, {'want_min': exp.get('min_verts')}
    return {'object_exists': obj_exists, 'verts_ok': verts_ok}

"""Phrasing augmentation v2: clean rewrite. Every template location-free;
the loc fragment is the ONLY position source. xN variants, execution-verified.
"""
from __future__ import annotations
import json, subprocess, tempfile
from pathlib import Path
import sys
sys.path.insert(0, '/home/egc365/dg-worktree/decision-gate')
from adapters import blender as B  # noqa: E402
from dataset.store import ExampleStore  # noqa: E402

# task: (template with {loc} exactly once, object, phrasings)
T = {
 'bbl-add-cube':  ("import bpy\nbpy.ops.mesh.primitive_cube_add({loc})", 'Cube',
   ["Add a cube","Create a cube mesh","Give me a cube","Put a cube in the scene","I need a cube"]),
 'bbl-suzanne':   ("import bpy\nbpy.ops.mesh.primitive_monkey_add({loc})", 'Suzanne',
   ["Add the monkey head","Add Suzanne","Put the Blender monkey in","Give me Suzanne","Monkey head please"]),
 'bbl-uv-sphere': ("import bpy\nbpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8{loc})", 'Sphere',
   ["Add a UV sphere","Create a sphere, 16 segments","Sphere with segments 16","I need a UV sphere"]),
 'bbl-torus':     ("import bpy\nbpy.ops.mesh.primitive_torus_add({loc})", 'Torus',
   ["Add a torus","Create a donut","Torus please","Put a torus in the scene"]),
 'bbl-cylinder':  ("import bpy\nbpy.ops.mesh.primitive_cylinder_add({loc})", 'Cylinder',
   ["Add a cylinder","Create a cylinder mesh","Cylinder please","I need a cylinder"]),
 'bbl-cone':      ("import bpy\nbpy.ops.mesh.primitive_cone_add(radius1=1{loc})", 'Cone',
   ["Add a cone","Create a cone mesh","Cone please","I need a cone"]),
 'bbl-icosphere': ("import bpy\nbpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2{loc})", 'Icosphere',
   ["Add an icosphere","Ico sphere subdivisions 2","Create an icosphere, subd 2"]),
 'bbl-circle':    ("import bpy\nbpy.ops.mesh.primitive_circle_add(vertices=12,fill_type='NGON'{loc})", 'Circle',
   ["Add a circle, 12 verts","Circle with twelve vertices","12-vertex circle please"]),
 'bbl-plane':     ("import bpy\nbpy.ops.mesh.primitive_plane_add(size=10{loc})", 'Plane',
   ["Add a ground plane","10-meter plane","Plane sized 10","Ground plane please"]),
 'bbl-grid':      ("import bpy\nbpy.ops.mesh.primitive_grid_add(x_subdivisions=10,y_subdivisions=10{loc})", 'Grid',
   ["Add a reference grid","10x10 grid","Grid for reference"]),
}
LOCS = [('', 'at the origin'), (',location=(2,0,0)', 'at x=2'), (',location=(-2,1,0)', 'off to the side')]
FRAMINGS = ['{p}', '{p} please.', 'Could you {p}?']

def main():
    store = ExampleStore('/home/egc365/dg-worktree/decision-gate/data/dataset')
    made = failed = 0
    for tid, (tmpl, obj, phrases) in T.items():
        for pi, phrase in enumerate(phrases):
            for li, (frag, _d) in enumerate(LOCS):
                fi = (pi + li) % len(FRAMINGS)
                f = FRAMINGS[fi].format(p=phrase)
                body = tmpl.replace('{loc}', frag)
                wd = tempfile.mkdtemp(prefix='aug-')
                real = body + f"\nbpy.ops.wm.save_as_mainfile(filepath='{wd}/out.blend')\nprint('DGOK')"
                r = subprocess.run([B.BLENDER, '-b', '--factory-startup', '-noaudio', '--python-expr', real],
                                   capture_output=True, text=True, timeout=120, cwd=wd)
                if 'DGOK' not in r.stdout:
                    failed += 1; continue
                try: st = B.probe(f'{wd}/out.blend')
                except Exception: failed += 1; continue
                names = [o['name'] for o in st['objects']]
                ok = obj in names
                store.add(task_id=tid, session_id=f'aug2-{pi}-{li}',
                          source_store='blender-aug-executed',
                          evidence_locator=f'blender:///{wd}/out.blend',
                          features={}, label='accept' if ok else 'reject',
                          reviewer='auto-executed-aug', synthetic=False,
                          notes=f'prompt={f} | completion={body} | v{pi}-{li}')
                made += 1 if ok else 0
    return {'verified': made, 'failed': failed}

if __name__ == '__main__':
    print(json.dumps(main()))

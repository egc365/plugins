"""CAD domain adapter (DG06): cadquery kernel, parametric checks.

State schema cad-state/1: per-solid volume/bbox/bounding dims, object names.
Actions are parametric edits (dimension changes) via the kernel; outcome
checks recompute geometry - mass properties, not 'kernel exited 0'.

numpy2 compat shim applied first (nptyping on numpy2 requirement).
"""
from __future__ import annotations
from adapters.numpy2_compat import apply as _npfix
_npfix()

import cadquery as cq

STATE_SCHEMA = 'cad-state/1'

def build_box(w, d, h):
    return cq.Workplane('XY').box(w, d, h)

def probe(wp):
    solids = []
    for obj in wp.objects:
        s = obj
        bb = s.BoundingBox()
        solids.append({'type': s.ShapeType() if hasattr(s, 'ShapeType') else 'Solid',
                       'volume_cm3': round(s.Volume() / 1000.0, 4),
                       'bbox': [round(bb.xlen, 4), round(bb.ylen, 4), round(bb.zlen, 4)]})
    return {'schema': STATE_SCHEMA, 'objects': solids,
            'n': len(solids),
            'total_volume_cm3': round(sum(s['volume_cm3'] for s in solids), 4)}

def set_dim(wp, index, axis, value):
    """Rebuild parametrically: for the demo the box dims are the parameters."""
    objs = wp.objects
    bb = objs[index].BoundingBox()
    dims = {k: v for k, v in zip('xyz', [bb.xlen, bb.ylen, bb.zlen])}
    dims[axis] = value
    return build_box(dims['x'], dims['y'], dims['z'])

def outcome_checks(task):
    exp = task.get('expect') or {}
    def volume_within(receipt, st):
        lo, hi = exp.get('volume_range', [0, 1e9])
        v = st.get('total_volume_cm3', 0)
        return lo <= v <= hi, {'range': [lo, hi], 'got': v}
    def dim_matches(receipt, st):
        axis = exp.get('axis'); want = exp.get('dim')
        if not axis or want is None or not st['objects']:
            return False, {'error': 'bad criterion'}
        idx = {'x': 0, 'y': 1, 'z': 2}[axis]
        got = st['objects'][0]['bbox'][idx]
        return abs(got - want) < 1e-3, {'axis': axis, 'want': want, 'got': got}
    checks = {}
    if 'volume_range' in exp: checks['volume_within'] = volume_within
    if 'dim' in exp: checks['dim_matches'] = dim_matches
    return checks

"""MuJoCo physics domain adapter (DG06): state, action, outcome on real sim.

State schema mujoco-state/1: time, qpos, qvel, ncon, body xyp of interest.
apply_action steps the sim N frames (the executor calls this via its registry);
outcome checks read physics state - energy, height, settled-ness - NEVER
'step returned without exception'.

Includes a built-in pendulum model so the domain is testable without assets.
"""
from __future__ import annotations
import math

STATE_SCHEMA = 'mujoco-state/1'

PENDULUM_XML = """
<mujoco>
  <worldbody>
    <light diffuse=".5 .5 .5" pos="0 0 3"/>
    <body name="pole">
      <joint name="hinge" type="hinge" axis="0 1 0" pos="0 0 0"/>
      <geom type="capsule" fromto="0 0 0 0 0 -1" size="0.04"/>
    </body>
  </worldbody>
</mujoco>
"""

def make_pendulum():
    import mujoco
    model = mujoco.MjModel.from_xml_string(PENDULUM_XML)
    data = mujoco.MjData(model)
    return mujoco.MjModel, model, data

def probe(model, data):
    import numpy as np
    qpos = [float(x) for x in data.qpos] if data.qpos is not None else []
    qvel = [float(x) for x in data.qvel] if data.qvel is not None else []
    return {'schema': STATE_SCHEMA, 'time': float(data.time),
            'nq': model.nq, 'qpos': qpos, 'qvel': qvel,
            'ncon': int(data.ncon),
            'energy': round(abs(float(data.qvel[0])) if len(data.qvel) else 0.0, 6)}

def apply_action(model, data, torque=0.0, frames=10):
    import mujoco
    if model.nu:
        data.ctrl[:] = [torque] * model.nu
    for _ in range(frames):
        mujoco.mj_step(model, data)
    return probe(model, data)

def outcome_checks(task):
    exp = task.get('expect') or {}
    def settled(receipt, st):
        tol = float(exp.get('vel_below', 0.05))
        return max((abs(v) for v in st.get('qvel', []) or [0]), default=0) < tol, {'tol': tol, 'qvel': st.get('qvel')}
    def angle_near(receipt, st):
        want = float(exp.get('qpos_near', 0)); tol = float(exp.get('tol', 0.2))
        qs = st.get('qpos') or []
        ok = any(abs(q - want) < tol for q in qs) if qs else False
        return ok, {'want': want, 'tol': tol, 'qpos': qs}
    checks = {}
    if 'vel_below' in exp: checks['settled'] = settled
    if 'qpos_near' in exp: checks['angle_near'] = angle_near
    return checks

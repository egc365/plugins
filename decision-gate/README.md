# decision-gate

Agent decision & verification system. See ../plans/decision-gate/BUILD-PROGRAM status below.

## Layout
- contracts/schemas.py   Proposal | Decision | ExecutionReceipt (dg1, hash-bound)
- executor/executor.py   permission/freshness/idempotency-guarded execution
- evaluator/outcome.py   task-completion checks on resulting_state (label_rev'd)
- providers/clients.py   Clef /v1/systemone + SGLang /v1/decisions clients
- host/capabilities.py   honest host probe (no fabricated schedulers)
- adapters/              blender | a11y | slack-bridge(ro) | mujoco | cad
- pilot/                 shadow loop + gate A/B harness
- experiments/           gate_ab (v1 FAIL baseline) + gate_ab_v2 (PASS)
- training/              micrograd baseline + 16-field documented features
- dataset/               versioned store, lineage splits, immutable holdout
- receipts/              machine evidence per DG
- gates/                 human-only merge/promotion/training-signoff rules

## Verify
    scripts/check.sh --unit DG01        # or DG02... tests are keyed
    python3 -m pytest tests --ignore=tests/adapters_live -q   # 38 pass
    # live adapters need their runtime (blender/a11y/mujoco/cad noted in receipts)

## Status (2026-10-27, round 25b)
7 surfaces: 6 domains live + d8 base TRAINED (400+800, both checkpoints
hash-gated 3895a039/a2510355, val bpb 1.1546@400 improving); 111-row blender
corpus (30 base + 81 phrasing-aug, execution-verified); gate arc v1 FAIL->
v2 PASS (enforcement-ready pending owner sign-off); decision serving LIVE
(:8765 shape + :30000 sglang native systemone); 21 PRs. Remaining: chatgpt
interactive validation; human label review; phrasing scale-out; front-end vision head.

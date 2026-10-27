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

## Status (2026-10-27, round 20)
6/7 domains live-verified; gate arc v1 FAIL -> v2 PASS (enforcement-ready,
pending owner sign-off); 325-row real dataset; 19 PRs chain.
LIVE decision serving: clef-flash /v1/systemone-shaped on :8761? no :8765
(systemd clef-serve) - 1553ms end-to-end, abstain paths verified.
Remaining: sglang native joint-head numerics; chatgpt interactive
validation; human label review; enforcement-at-N.

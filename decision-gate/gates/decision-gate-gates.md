# Program gates (owner directive)
- Human-only: PR merges, model-promotion, deployment-promotion.
- Training gate: before ANY task-specific weight training, present model, dataset
  provenance, loss, compute estimate, eval criteria; await owner sign-off.
- Shadow-first: classifier recommendations recorded, never controlling
  execution until DG04 correctness+execution checks pass.
- Budget ceiling $250 across providers; verify metering pre-launch.
- Evaluation/holdout labels immutable during an experiment; changes = new version.

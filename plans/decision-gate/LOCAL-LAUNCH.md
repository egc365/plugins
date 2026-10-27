# Local launch handoff

Read BUILD-PLAN.md in this directory and the actual PStack skills in this repository. This is a build authorization, not evidence that any implementation or training already exists.

Use poteto-mode's multi-phase-plan playbook for the board, its orchestrate playbook for coordination, and figure-it-out for bounded implementation. Adapt unavailable host tools explicitly. Do not assume Cursor's cloud orchestrator can spend another provider's credits.

1. Discover the authenticated GitHub owner and local application checkout. Reuse existing relevant forks. Read AGENTS.md and repository instructions before edits. Keep private repository names, source, credentials, traces, and budget configuration out of public commits.
2. Inventory the public repositories in REPOSITORIES.md. Pin actual commit SHAs and licenses. Discover a micrograd fork; if absent, fork karpathy/micrograd into the user's account. Do not duplicate existing forks or download every repository and model.
3. Implement DG01 through DG06 in dependency order. Use isolated branches/worktrees, at most three workers, a fresh verifier, and at most two repair retries per failure. Record exact heads and evidence. Never turn a missing implementation, unavailable environment, or skipped check into a pass.
4. Build a portable skills/MCP plugin adapter for the actual host. Explicitly map missing Task, timer, hook, and local process capabilities. A package being committed does not mean it is installed or its service deployed.
5. Start with a real shell and trace-UI pilot in shadow mode. Keep classifier decision, optional repair selection, generative repair author, and executor separate. State hashes identify snapshots; meaningful goal/state/action features are still required. Validate stale-state rejection and idempotency before enforcement.
6. Include micrograd as a tiny, inspectable classifier training baseline. Its autograd computes derivatives; the action evaluator supplies correctness labels. Check gradients against finite differences and PyTorch. Use genuine, provenance-recorded labels for task evaluation. Synthetic fixtures may test plumbing only and must be labeled as such. Large-model adaptation uses an appropriate tensor framework, not micrograd's scalar engine.
7. Reuse autoresearch's bounded experiment pattern, with an immutable evaluator and separate held-out data. Do not let the optimization loop edit its grading rules. Implement training preparation now; begin weight training only after the recorded model, feature, dataset, and evaluation design sign-off. Do not invent reasoning traces or assume a provider exposes hidden reasoning.
8. Read the user's local budget cap and verify the actual credit provider, eligible services, current rates, and metering before paid jobs. Reserve funds for in-flight work and shutdown. Stop paid launches before exceeding the cap. If reliable metering is unavailable, continue unpaid implementation and report the blocker.
9. Leave merges, deployment promotion, and model promotion to the owner. Return branches/PRs, reproducible commands, source citations, measured results, costs, and remaining blockers. Never claim the full system works based only on mock tests.

Begin with repository discovery and DG01. Continue all independent implementation when one optional environment is unavailable.

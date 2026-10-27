# Build the decision gate with PStack

Build an application decision gate that evaluates proposed actions with existing Jev-compatible models.
Reuse the owner's GitHub forks and local application integrations.
Keep model judgments separate from execution authorization.
Deliver a ChatGPT Work-compatible plugin package and a locally verified service.
Run DG01, then DG02 and DG03, then DG04, DG05, and DG06.
This file is a build contract. No implementation, model benchmark, or hardware test is claimed here.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. Check a box only when its evidence exists. Evidence can be a committed file, run log, screenshot, result table, or exact head SHA. Keep unchecked boxes unchecked until the named evidence exists.

The program runs `pstack/skills/poteto-mode/playbooks/orchestrate.md` from the owner's PStack fork. Use `figure-it-out` for a bounded pilot that fits one session. The local Fable session coordinates workers through the tools actually available in that host. The operator merges and promotes every PR. All six PRs stop at merge-ready.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

All paths under `decision-gate/` below are proposed implementation targets in the plugin fork. They are not claims about existing files. DG01 creates the command contract. A command whose implementation is missing must exit nonzero with `NOT_IMPLEMENTED`.

This plan adapts PStack to the available host. Ten live lanes are ten scenarios, not a requirement to buy ten cloud machines. Run independent scenarios sequentially or with at most three workers. Resolve `inherit-parent` to the actual model ID and record it. Use a different model family for judgment review when available. Record a missing capability rather than claiming it ran.

## Program checklist

### Arm the program

- [ ] Record the user's existing authorization to build and evaluate. Do not ask for another routine start confirmation. Record human-only merge, model-training, and deployment gates in `orchestrate/decision-gate/gates.md`.
- [ ] Read the PStack source pinned at `99743e9c151c8537cbbf1f98bb38f34ef3368453`. Compare the locally installed version before adapting it. Read `git show origin/main:pstack/skills/poteto-mode/playbooks/orchestrate.md`, `pstack/skills/swarm/SKILL.md`, the selected control skills, `pstack/skills/poteto-mode/playbooks/opening-a-pr.md`, and every leaf skill actually used. Record source SHAs.
- [ ] Inspect the host's real task and scheduling tools. Use `/loop 1h` only if a real local loop implementation exists. Otherwise use explicit bounded coordinator cycles and record the lack of background scheduling.
- [ ] Use the following audit tick. Re-read the execution playbook. Compare active tasks with pushed commits, receipts, and current head SHAs. Repair drift, reconcile stuck workers, and append the decision trail. Send a status message only for a new result, blocker, changed head, or required operator decision. Never claim a timer exists because a prompt contains slash text.
- [ ] Configure the local spending ceiling and provider meters before paid work. Reserve estimated in-flight cost before each launch. Stop paid launches if the remaining budget or billing identity cannot be established. Keep balances and credentials out of public files.
- [ ] On a hold instruction, send all workers a zero-writes order and record their acknowledged states.

### Spawn owners

- [ ] Give one owner each PR. Use at most three concurrent workers initially. Give each writer an exclusive branch and worktree.
- [ ] Run DG01 first. Run DG02 and DG03 independently after DG01. Run DG04 after both. Run DG05 after DG04. Run DG06 after DG05. Dependencies may use reviewed parent branches without merging them.
- [ ] Keep DG02 in `decision-gate/host/` and plugin packaging. Keep DG03 in `decision-gate/providers/` and serving recipes. Resolve shared contract edits through the DG01 owner.
- [ ] Give each brief a goal, allowed paths, forbidden paths, source pointers, acceptance checks, commands, timebox, budget reservation, and required receipts.
- [ ] Use at most two retries per failed unit. After two failures, change the approach or record a blocker. Do not retry unchanged work indefinitely.

### PR mechanics, for every PR

- [ ] Reuse the owner's existing forks. Record upstream, branch, exact SHA, license, and intended use before cloning. Fork a missing dependency when its code must change or the owner explicitly requested a fork, including micrograd. Do not clone unrelated repositories or copy model weights into Git.
- [ ] Read each target repository's `AGENTS.md` and local instructions before edits. Preserve existing work. Keep private application sources and traces in their private repository or local storage.
- [ ] Resolve the forge from installed tools. Use the connected GitHub tools or `gh`. Never assume a command exists because PStack names it.
- [ ] Create one reviewable PR per unit with its dependencies and evidence. Keep incomplete work visibly incomplete. Do not merge or retarget another owner's PR.
- [ ] Run available lint and type checks, then source review before each review-ready push. Apply PStack writing and review skills from the pinned source. Record unavailable tools as unavailable.

### Verdict and merge, for every PR

- [ ] Key each verification record by repository, PR, head SHA, dataset revision, model revision, and runtime configuration. A code change invalidates affected checks.
- [ ] Use `PASS`, `FAIL`, `BLOCKED`, or `NOT_RUN` for every check. A missing GPU, application, dataset, or host integration is not a pass.
- [ ] Inspect worker output and receipts. A summary or green CI is not proof of model quality or an app interaction.
- [ ] The operator alone merges and promotes verified changes. Keep model training disabled until the operator approves the dataset, objective, and frozen evaluation gates.

### Boot recipe, for every live lane

- [ ] Create an isolated worktree at the recorded PR head. Capture the previous app state and the exact runtime configuration without credentials.
- [ ] Start only project-owned services on discovered free ports. Do not stop or replace existing services. Wait for health checks, then verify the expected model and route.
- [ ] Use `control-cli` for a real command-line workflow and `control-ui` for browser or Electron workflows when those skills exist. Otherwise record the actual supported equivalent and its limits.
- [ ] Run the named `scripts/live-check.sh --case` scenario from the `decision-gate/` directory. Save a machine-readable receipt and the specified screenshot of the real CLI or app. A screenshot alone does not prove the model result.
- [ ] Store private screenshots and raw traces locally. Public receipts contain hashes, sanitized descriptions, and safe locators only.

## Inventory the forks and freeze the contracts (DG01)

**Depends on.** None.

**Files.**

- [ ] Create or extend `docs/decision-gate/repositories.json`. Record the exact resulting files in the PR.
- [ ] Create or extend `decision-gate/contracts/`. Record the exact resulting files in the PR.
- [ ] Create or extend `decision-gate/scripts/`. Record the exact resulting files in the PR.
- [ ] Create or extend `decision-gate/tests/contracts/`. Record the exact resulting files in the PR.

**Build.**

- [ ] Resolve the runtime checkout and application plugin seam. Inventory all accessible repositories by metadata, then read only relevant repositories. Keep private mappings in a separate local manifest. Define Proposal, Decision, and ExecutionReceipt schemas. Include schema version, task and app IDs, goal, readable state, state version and hash, proposed action and hash, constraints, timestamps, expiry, idempotency key, model and runtime revisions, route, probabilities, decision status, evidence locators, and execution result. Define reject, accept, and abstain as service states. An accept verdict never grants authorization. Create scripts/check.sh, scripts/live-check.sh, and scripts/bench.sh with explicit missing-implementation failures. Freeze resource limits, evaluation splits, and metric definitions before downstream runs.

**You see.**

- [ ] A reproducible inventory and contract validation receipt identify every source and dependency without exposing private data. Save `receipts/DG01/summary.json`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `scripts/check.sh --unit DG01` from `decision-gate/`. Save `receipts/DG01/unit.log` with the command, exit status, and head SHA. Verify malformed input and failure handling as well as success.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `inherit-parent` at the PR head. Resolve the model ID before launch. Run the lanes as separate scenarios under the shared boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run `scripts/live-check.sh --case dg01-inventory`. Save `receipts/DG01/inventory.png` and its JSON receipt. Pass when the observed upstream and SHA match GitHub and the local checkout.
- [ ] Lane 2. Run `scripts/live-check.sh --case dg01-private-manifest`. Save `receipts/DG01/private-manifest.png` and its JSON receipt. Pass when public output contains no private repository mapping or credentials.
- [ ] Lane 3. Run `scripts/live-check.sh --case dg01-missing-check`. Save `receipts/DG01/missing-check.png` and its JSON receipt. Pass when an unimplemented command exits nonzero with NOT_IMPLEMENTED.
- [ ] Lane 4. Run `scripts/live-check.sh --case dg01-valid-proposal`. Save `receipts/DG01/valid-proposal.png` and its JSON receipt. Pass when a complete proposal round-trips without field loss.
- [ ] Lane 5. Run `scripts/live-check.sh --case dg01-missing-goal`. Save `receipts/DG01/missing-goal.png` and its JSON receipt. Pass when a proposal missing its goal is rejected at the boundary.
- [ ] Lane 6. Run `scripts/live-check.sh --case dg01-bad-probability`. Save `receipts/DG01/bad-probability.png` and its JSON receipt. Pass when naN and probabilities outside zero to one are rejected.
- [ ] Lane 7. Run `scripts/live-check.sh --case dg01-expired-proposal`. Save `receipts/DG01/expired-proposal.png` and its JSON receipt. Pass when an expired proposal cannot be executable.
- [ ] Lane 8. Run `scripts/live-check.sh --case dg01-schema-version`. Save `receipts/DG01/schema-version.png` and its JSON receipt. Pass when an unsupported schema version fails explicitly.
- [ ] Lane 9. Run `scripts/live-check.sh --case dg01-hash-binding`. Save `receipts/DG01/hash-binding.png` and its JSON receipt. Pass when changing action or state invalidates the prior binding.
- [ ] Lane 10. Run `scripts/live-check.sh --case dg01-budget-reservation`. Save `receipts/DG01/budget-reservation.png` and its JSON receipt. Pass when a launch that exceeds locally configured remaining funds is refused.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Inventory duration, schema-validation p95 latency, and peak process memory.
- [ ] Probe. Run scripts/bench.sh --unit DG01 against the recorded trunk behavior and head in alternating order. Record absent trunk capabilities explicitly.
- [ ] Baseline. Record trunk results first with hardware, app, model, concurrency, and input-size metadata. If trunk lacks the feature, record that fact and benchmark the added work directly.
- [ ] Rule. Before candidate tuning, freeze numeric absolute budgets and the allowed regression percentage in `eval-policy.json` using the initial baseline. Fail if a required budget is absent, a budget is exceeded, or a safety invariant fails. Require zero unauthorized, duplicate, and stale-state executions. Do not claim a ratio for unlike work.

**Review gate.** The operator reviews before merge.

- [ ] Present a screenshot of the real result and a short video for the changed interaction. Link the exact head SHA and required receipts. Keep operator merge approval separate from model acceptance.

**Merge.**

- [ ] Obtain an independent review where available. Reconcile the exact PR head with its verification ledger. Present any unavailable review as a limitation. The operator alone merges or promotes this unit.

## Adapt PStack and package the Work plugin (DG02)

**Depends on.** DG01.

**Files.**

- [ ] Create or extend `decision-gate/host/`. Record the exact resulting files in the PR.
- [ ] Create or extend `decision-gate/plugin/`. Record the exact resulting files in the PR.
- [ ] Create or extend `decision-gate/tests/host/`. Record the exact resulting files in the PR.
- [ ] Create or extend `docs/decision-gate/host-support.md`. Record the exact resulting files in the PR.

**Build.**

- [ ] Create a separate host adapter that reuses pinned PStack skills and preserves their attribution and license. Map task delegation, filesystem access, GitHub writes, model selection, scheduling, and receipts to discovered host capabilities. Keep local Fable and ChatGPT Work profiles separate. Verify the current official plugin manifest and distribution schema before generating the package. Make cloud Work operate without local shell hooks. Expose evaluation and status tools through an authenticated MCP boundary when the local service must be reached remotely. Do not expose an unrestricted shell tool. A skill-only package must say that it cannot contact local inference. Preserve existing Cursor behavior.

**You see.**

- [ ] A supported host discovers the plugin and invokes a documented capability. Missing capabilities produce an explicit supported fallback or BLOCKED result. Save `receipts/DG02/summary.json`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `scripts/check.sh --unit DG02` from `decision-gate/`. Save `receipts/DG02/unit.log` with the command, exit status, and head SHA. Verify malformed input and failure handling as well as success.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `inherit-parent` at the PR head. Resolve the model ID before launch. Run the lanes as separate scenarios under the shared boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run `scripts/live-check.sh --case dg02-host-regression`. Save `receipts/DG02/host-regression.png` and its JSON receipt. Pass when existing PStack invocation still works at trunk and head.
- [ ] Lane 2. Run `scripts/live-check.sh --case dg02-work-load`. Save `receipts/DG02/work-load.png` and its JSON receipt. Pass when work discovers the packaged skill with correct metadata.
- [ ] Lane 3. Run `scripts/live-check.sh --case dg02-local-load`. Save `receipts/DG02/local-load.png` and its JSON receipt. Pass when the local app loads the profile without editing global PStack files.
- [ ] Lane 4. Run `scripts/live-check.sh --case dg02-task-mapping`. Save `receipts/DG02/task-mapping.png` and its JSON receipt. Pass when a real delegated task returns its receipt and actual model ID.
- [ ] Lane 5. Run `scripts/live-check.sh --case dg02-missing-task`. Save `receipts/DG02/missing-task.png` and its JSON receipt. Pass when no Task call is fabricated when delegation is unavailable.
- [ ] Lane 6. Run `scripts/live-check.sh --case dg02-no-cloud-hooks`. Save `receipts/DG02/no-cloud-hooks.png` and its JSON receipt. Pass when the cloud profile completes its status flow without local hooks.
- [ ] Lane 7. Run `scripts/live-check.sh --case dg02-auth-denied`. Save `receipts/DG02/auth-denied.png` and its JSON receipt. Pass when an unauthenticated MCP request cannot inspect private state.
- [ ] Lane 8. Run `scripts/live-check.sh --case dg02-tool-scope`. Save `receipts/DG02/tool-scope.png` and its JSON receipt. Pass when the exposed tool schema cannot execute arbitrary shell text.
- [ ] Lane 9. Run `scripts/live-check.sh --case dg02-scheduler-missing`. Save `receipts/DG02/scheduler-missing.png` and its JSON receipt. Pass when a missing scheduler is reported without claiming a loop is active.
- [ ] Lane 10. Run `scripts/live-check.sh --case dg02-package-reinstall`. Save `receipts/DG02/package-reinstall.png` and its JSON receipt. Pass when reinstalling the same version preserves settings and avoids duplicate entries.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Plugin load time, status-call p95 latency, and host adapter overhead.
- [ ] Probe. Run scripts/bench.sh --unit DG02 against the same supported host on trunk and head. Compare unchanged status paths and measure newly added paths separately.
- [ ] Baseline. Record trunk results first with hardware, app, model, concurrency, and input-size metadata. If trunk lacks the feature, record that fact and benchmark the added work directly.
- [ ] Rule. Before candidate tuning, freeze numeric absolute budgets and the allowed regression percentage in `eval-policy.json` using the initial baseline. Fail if a required budget is absent, a budget is exceeded, or a safety invariant fails. Require zero unauthorized, duplicate, and stale-state executions. Do not claim a ratio for unlike work.

**Review gate.** The operator reviews before merge.

- [ ] Present a screenshot of the real result and a short video for the changed interaction. Link the exact head SHA and required receipts. Keep operator merge approval separate from model acceptance.

**Merge.**

- [ ] Obtain an independent review where available. Reconcile the exact PR head with its verification ledger. Present any unavailable review as a limitation. The operator alone merges or promotes this unit.

## Connect the existing decision models (DG03)

**Depends on.** DG01.

**Files.**

- [ ] Create or extend `decision-gate/providers/`. Record the exact resulting files in the PR.
- [ ] Create or extend `decision-gate/serving/`. Record the exact resulting files in the PR.
- [ ] Create or extend `decision-gate/tests/providers/`. Record the exact resulting files in the PR.

**Build.**

- [ ] Implement separate Clef SystemOne and generic SGLang decision clients. Use /v1/systemone for Clef Flash and Clef. Use /v1/decisions for supported ordinary Qwen models. Detect model identity, tokenizer requirements, image support, and response semantics. Preserve the original probability and confidence fields without conflating them. Serialize outputs in application code. Pin weights, tokenizer, container digest, and SGLang revision. Inspect the existing Spark serving fork before creating an ARM64 recipe. Verify Clef custom-head support separately from ordinary Qwen support. Record a real text and image request for every supported configuration. Keep timeouts and malformed replies as abstain outcomes.

**You see.**

- [ ] A live model returns bounded decisions with its exact model revision and route. An unavailable backend is visible and cannot approve an action. Save `receipts/DG03/summary.json`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `scripts/check.sh --unit DG03` from `decision-gate/`. Save `receipts/DG03/unit.log` with the command, exit status, and head SHA. Verify malformed input and failure handling as well as success.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `inherit-parent` at the PR head. Resolve the model ID before launch. Run the lanes as separate scenarios under the shared boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run `scripts/live-check.sh --case dg03-provider-regression`. Save `receipts/DG03/provider-regression.png` and its JSON receipt. Pass when existing read-only status requests behave the same on trunk and head.
- [ ] Lane 2. Run `scripts/live-check.sh --case dg03-clef-text`. Save `receipts/DG03/clef-text.png` and its JSON receipt. Pass when clef returns valid probabilities through /v1/systemone.
- [ ] Lane 3. Run `scripts/live-check.sh --case dg03-flash-text`. Save `receipts/DG03/flash-text.png` and its JSON receipt. Pass when clef Flash returns valid probabilities through /v1/systemone.
- [ ] Lane 4. Run `scripts/live-check.sh --case dg03-qwen-text`. Save `receipts/DG03/qwen-text.png` and its JSON receipt. Pass when a compatible Qwen model answers through /v1/decisions.
- [ ] Lane 5. Run `scripts/live-check.sh --case dg03-wrong-route`. Save `receipts/DG03/wrong-route.png` and its JSON receipt. Pass when a Clef request cannot silently fall back to chat generation.
- [ ] Lane 6. Run `scripts/live-check.sh --case dg03-image-decision`. Save `receipts/DG03/image-decision.png` and its JSON receipt. Pass when a real image is processed and the receipt records its hash.
- [ ] Lane 7. Run `scripts/live-check.sh --case dg03-timeout`. Save `receipts/DG03/timeout.png` and its JSON receipt. Pass when a timed-out model produces abstain and zero execution.
- [ ] Lane 8. Run `scripts/live-check.sh --case dg03-malformed-response`. Save `receipts/DG03/malformed-response.png` and its JSON receipt. Pass when malformed or incomplete probabilities fail closed.
- [ ] Lane 9. Run `scripts/live-check.sh --case dg03-model-mismatch`. Save `receipts/DG03/model-mismatch.png` and its JSON receipt. Pass when the service rejects an unexpected served model or revision.
- [ ] Lane 10. Run `scripts/live-check.sh --case dg03-arm64-smoke`. Save `receipts/DG03/arm64-smoke.png` and its JSON receipt. Pass when the exact recorded ARM64 configuration completes a real request without unsupported-kernel errors.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Warm and cold decision p50 and p95 latency, input size, peak memory, and backend error rate.
- [ ] Probe. Run scripts/bench.sh --unit DG03 on unchanged model weights with interleaved direct-backend and wrapped-backend requests. Record unavailable trunk endpoints rather than inventing ratios.
- [ ] Baseline. Record trunk results first with hardware, app, model, concurrency, and input-size metadata. If trunk lacks the feature, record that fact and benchmark the added work directly.
- [ ] Rule. Before candidate tuning, freeze numeric absolute budgets and the allowed regression percentage in `eval-policy.json` using the initial baseline. Fail if a required budget is absent, a budget is exceeded, or a safety invariant fails. Require zero unauthorized, duplicate, and stale-state executions. Do not claim a ratio for unlike work.

**Review gate.** The operator reviews before merge.

- [ ] Present a screenshot of the real result and a short video for the changed interaction. Link the exact head SHA and required receipts. Keep operator merge approval separate from model acceptance.

**Merge.**

- [ ] Obtain an independent review where available. Reconcile the exact PR head with its verification ledger. Present any unavailable review as a limitation. The operator alone merges or promotes this unit.

## Build the shell and trace application pilot (DG04)

**Depends on.** DG02 and DG03.

**Files.**

- [ ] Create or extend `decision-gate/adapters/shell/`. Record the exact resulting files in the PR.
- [ ] Create or extend `decision-gate/adapters/trace_ui/`. Record the exact resulting files in the PR.
- [ ] Create or extend `decision-gate/runtime/`. Record the exact resulting files in the PR.
- [ ] Create or extend `decision-gate/tests/pilot/`. Record the exact resulting files in the PR.

**Build.**

- [ ] Attach state extraction to the existing application seam instead of replacing the host. Start in shadow mode. Record the proposed action, decision, and observed outcome without changing execution. Add opt-in enforcement only for explicitly authorized allowlisted test actions. Bind each decision to the current state version, exact action hash, expiry, and idempotency key. Recheck state at execution time. The executor enforces permissions independently of model confidence. Return rejected actions to the existing agent. Permit repair selection only from supplied candidates with a none-suitable option. Keep generated repair writing outside the classifier.

**You see.**

- [ ] The trace UI shows an action, its model verdict, its evidence, and whether authorized execution occurred. Shell results can be replayed from receipts. Save `receipts/DG04/summary.json`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `scripts/check.sh --unit DG04` from `decision-gate/`. Save `receipts/DG04/unit.log` with the command, exit status, and head SHA. Verify malformed input and failure handling as well as success.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `inherit-parent` at the PR head. Resolve the model ID before launch. Run the lanes as separate scenarios under the shared boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run `scripts/live-check.sh --case dg04-pilot-regression`. Save `receipts/DG04/pilot-regression.png` and its JSON receipt. Pass when the unchanged observation workflow matches trunk and adds no unintended execution.
- [ ] Lane 2. Run `scripts/live-check.sh --case dg04-shadow-accept`. Save `receipts/DG04/shadow-accept.png` and its JSON receipt. Pass when an accept verdict in shadow mode does not trigger execution.
- [ ] Lane 3. Run `scripts/live-check.sh --case dg04-shadow-reject`. Save `receipts/DG04/shadow-reject.png` and its JSON receipt. Pass when a reject verdict is recorded without mutating the application.
- [ ] Lane 4. Run `scripts/live-check.sh --case dg04-authorized-accept`. Save `receipts/DG04/authorized-accept.png` and its JSON receipt. Pass when an allowed action executes exactly once after independent authorization.
- [ ] Lane 5. Run `scripts/live-check.sh --case dg04-unauthorized-accept`. Save `receipts/DG04/unauthorized-accept.png` and its JSON receipt. Pass when a confident accept cannot bypass the executor permissions.
- [ ] Lane 6. Run `scripts/live-check.sh --case dg04-stale-state`. Save `receipts/DG04/stale-state.png` and its JSON receipt. Pass when changing state between judgment and execution blocks the old decision.
- [ ] Lane 7. Run `scripts/live-check.sh --case dg04-duplicate-action`. Save `receipts/DG04/duplicate-action.png` and its JSON receipt. Pass when retrying an idempotency key cannot execute the action twice.
- [ ] Lane 8. Run `scripts/live-check.sh --case dg04-unknown-state`. Save `receipts/DG04/unknown-state.png` and its JSON receipt. Pass when missing required observations produce abstain.
- [ ] Lane 9. Run `scripts/live-check.sh --case dg04-repair-choice`. Save `receipts/DG04/repair-choice.png` and its JSON receipt. Pass when the classifier selects only a supplied candidate or none suitable.
- [ ] Lane 10. Run `scripts/live-check.sh --case dg04-outcome-check`. Save `receipts/DG04/outcome-check.png` and its JSON receipt. Pass when a successful process exit with an incorrect task postcondition is recorded as task failure.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. End-to-end decision-to-observed-result latency, extraction overhead, duplicate execution count, and stale-decision execution count.
- [ ] Probe. Run scripts/bench.sh --unit DG04 with the same safe shell and trace-app tasks at trunk and head. Measure added gating cost separately from model service time.
- [ ] Baseline. Record trunk results first with hardware, app, model, concurrency, and input-size metadata. If trunk lacks the feature, record that fact and benchmark the added work directly.
- [ ] Rule. Before candidate tuning, freeze numeric absolute budgets and the allowed regression percentage in `eval-policy.json` using the initial baseline. Fail if a required budget is absent, a budget is exceeded, or a safety invariant fails. Require zero unauthorized, duplicate, and stale-state executions. Do not claim a ratio for unlike work.

**Review gate.** The operator reviews before merge.

- [ ] Present a screenshot of the real result and a short video for the changed interaction. Link the exact head SHA and required receipts. Keep operator merge approval separate from model acceptance.

**Merge.**

- [ ] Obtain an independent review where available. Reconcile the exact PR head with its verification ledger. Present any unavailable review as a limitation. The operator alone merges or promotes this unit.

## Build the evaluator and bounded research loop (DG05)

**Depends on.** DG04.

**Files.**

- [ ] Create or extend `decision-gate/eval/`. Record the exact resulting files in the PR.
- [ ] Create or extend `decision-gate/research/` and `decision-gate/training/micrograd/`. Record the exact resulting files in the PR.
- [ ] Create or extend `decision-gate/tests/eval/`. Record the exact resulting files in the PR.
- [ ] Create or extend `docs/decision-gate/evaluation.md`. Record the exact resulting files in the PR.

**Build.**

- [ ] Build the app-action grader from verified postconditions and reviewed real traces. Reuse the experiment-recording and keep-or-discard pattern from the existing autoresearch fork. Do not treat its language-model val_bpb metric as an app-action metric. Keep the evaluator and labels immutable to optimizing workers. Separate training, development, and final holdout by task/session lineage. Freeze thresholds and dataset revisions before final scoring. Report false accepts, false rejects, abstention coverage, calibration, per-app results, latency, and confidence intervals. Count failed and timed-out requests. Run bounded schema, threshold, and runtime experiments before any weight training. Keep model training gated. Store raw private traces outside public Git. Include Karpathy's micrograd as a tiny classifier training baseline. Reuse an existing owner fork if discovered, otherwise fork the verified upstream. Its scalar autograd engine computes gradients; the separate action evaluator supplies labels. Define a documented feature schema before choosing input width. Implement a reproducible training entrypoint with recorded seed, loss, optimizer, data revision, and parameter count. Verify gradients against finite differences and PyTorch, including zeroing and repeated backward behavior. Prepare this code now and run the task-training pilot after design sign-off. Compare it with a constant predictor and the existing decision-model baseline on the same held-out tasks. Do not use scalar micrograd as the training engine for billion-parameter Clef models. Treat synthetic fixtures only as plumbing checks, never as evidence of task accuracy.

**You see.**

- [ ] A repeated evaluation at the same revision reproduces the report within declared numerical tolerances. An optimizer cannot improve its score by editing the grader. Save `receipts/DG05/summary.json`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `scripts/check.sh --unit DG05` from `decision-gate/`. Save `receipts/DG05/unit.log` with the command, exit status, and head SHA. Verify malformed input and failure handling as well as success.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `inherit-parent` at the PR head. Resolve the model ID before launch. Run the lanes as separate scenarios under the shared boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run `scripts/live-check.sh --case dg05-eval-regression`. Save `receipts/DG05/eval-regression.png` and its JSON receipt. Pass when previously verified task postconditions keep their labels at the same dataset revision.
- [ ] Lane 2. Run `scripts/live-check.sh --case dg05-real-provenance`. Save `receipts/DG05/real-provenance.png` and its JSON receipt. Pass when every scored record has a real trace and review provenance.
- [ ] Lane 3. Run `scripts/live-check.sh --case dg05-split-leakage`. Save `receipts/DG05/split-leakage.png` and its JSON receipt. Pass when shared task or session lineage across protected splits fails validation.
- [ ] Lane 4. Run `scripts/live-check.sh --case dg05-grader-lock`. Save `receipts/DG05/grader-lock.png` and its JSON receipt. Pass when a candidate that changes evaluator or labels is rejected.
- [ ] Lane 5. Run `scripts/live-check.sh --case dg05-timeout-count`. Save `receipts/DG05/timeout-count.png` and its JSON receipt. Pass when model timeouts remain in denominators and error reports.
- [ ] Lane 6. Run `scripts/live-check.sh --case dg05-false-accept`. Save `receipts/DG05/false-accept.png` and its JSON receipt. Pass when a known failed task accepted by the model increments false accepts.
- [ ] Lane 7. Run `scripts/live-check.sh --case dg05-abstention`. Save `receipts/DG05/abstention.png` and its JSON receipt. Pass when abstention coverage is reported separately from accepted-case accuracy.
- [ ] Lane 8. Run `scripts/live-check.sh --case dg05-holdout-lock`. Save `receipts/DG05/holdout-lock.png` and its JSON receipt. Pass when an optimization worker cannot read or tune against final holdout labels.
- [ ] Lane 9. Run `scripts/live-check.sh --case dg05-budget-stop`. Save `receipts/DG05/budget-stop.png` and its JSON receipt. Pass when the experiment loop stops before exceeding the configured reserved budget.
- [ ] Lane 10. Run `scripts/live-check.sh --case dg05-repeat-eval`. Save `receipts/DG05/repeat-eval.png` and its JSON receipt. Pass when a fixed model and dataset run reproduces metrics within the frozen tolerance.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Evaluation throughput, decision latency, false-accept rate, coverage, calibration, and confidence-interval width.
- [ ] Probe. Run scripts/bench.sh --unit DG05 with the same frozen cases and model revisions at trunk and head. Compare only equivalent graders. Record final holdout access once per approved evaluation cycle.
- [ ] Baseline. Record trunk results first with hardware, app, model, concurrency, and input-size metadata. If trunk lacks the feature, record that fact and benchmark the added work directly.
- [ ] Rule. Before candidate tuning, freeze numeric absolute budgets and the allowed regression percentage in `eval-policy.json` using the initial baseline. Fail if a required budget is absent, a budget is exceeded, or a safety invariant fails. Require zero unauthorized, duplicate, and stale-state executions. Do not claim a ratio for unlike work.

**Review gate.** The operator reviews before merge.

- [ ] Present a screenshot of the real result and a short video for the changed interaction. Link the exact head SHA and required receipts. Keep operator merge approval separate from model acceptance.

**Merge.**

- [ ] Obtain an independent review where available. Reconcile the exact PR head with its verification ledger. Present any unavailable review as a limitation. The operator alone merges or promotes this unit.

## Complete the domain adapters and hand off the plugin (DG06)

**Depends on.** DG05.

**Files.**

- [ ] Create or extend `decision-gate/adapters/blender/`. Record the exact resulting files in the PR.
- [ ] Create or extend `decision-gate/adapters/accessibility/`. Record the exact resulting files in the PR.
- [ ] Create or extend `decision-gate/adapters/mujoco/`. Record the exact resulting files in the PR.
- [ ] Create or extend `decision-gate/adapters/cad/`. Record the exact resulting files in the PR.
- [ ] Create or extend `decision-gate/adapters/slack_bridge/`. Record the exact resulting files in the PR.
- [ ] Create or extend `decision-gate/docs/`. Record the exact resulting files in the PR.
- [ ] Create or extend `decision-gate/tests/domains/`. Record the exact resulting files in the PR.

**Build.**

- [ ] Implement each remaining adapter using the host application API, accessibility tree, or verified state extraction. Include screenshots only when the task needs visual evidence. Give each domain its own state schema, question set, real evaluation cases, and receipt checks. Treat slack_bridge as dry-run outbound intent classification and recorded test messages. Do not send live messages. Reuse the proven executor boundary and state freshness checks. Package reproducible installation, capability detection, model configuration, rollback, and upgrade instructions. Publish one domain support matrix that distinguishes implemented, live-verified, blocked, and unsupported. Missing CAD or simulator software blocks that domain rather than the whole build.

**You see.**

- [ ] All seven domains have concrete adapters and evaluation receipts, or individually named blockers. A fresh installation can run the verified pilot and inspect the same results. Save `receipts/DG06/summary.json`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `scripts/check.sh --unit DG06` from `decision-gate/`. Save `receipts/DG06/unit.log` with the command, exit status, and head SHA. Verify malformed input and failure handling as well as success.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `inherit-parent` at the PR head. Resolve the model ID before launch. Run the lanes as separate scenarios under the shared boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run `scripts/live-check.sh --case dg06-domain-regression`. Save `receipts/DG06/domain-regression.png` and its JSON receipt. Pass when the shell and trace pilot still passes unchanged at trunk and head.
- [ ] Lane 2. Run `scripts/live-check.sh --case dg06-blender-object`. Save `receipts/DG06/blender-object.png` and its JSON receipt. Pass when a real object-state change is observed and bound to the correct action.
- [ ] Lane 3. Run `scripts/live-check.sh --case dg06-accessibility-focus`. Save `receipts/DG06/accessibility-focus.png` and its JSON receipt. Pass when a focus change invalidates a decision bound to the previous target.
- [ ] Lane 4. Run `scripts/live-check.sh --case dg06-mujoco-state`. Save `receipts/DG06/mujoco-state.png` and its JSON receipt. Pass when a simulator-state mismatch blocks the stale proposed action.
- [ ] Lane 5. Run `scripts/live-check.sh --case dg06-cad-document`. Save `receipts/DG06/cad-document.png` and its JSON receipt. Pass when a changed document revision invalidates the old decision.
- [ ] Lane 6. Run `scripts/live-check.sh --case dg06-slack-dry-run`. Save `receipts/DG06/slack-dry-run.png` and its JSON receipt. Pass when an outbound intent produces a receipt and sends zero live messages.
- [ ] Lane 7. Run `scripts/live-check.sh --case dg06-domain-isolation`. Save `receipts/DG06/domain-isolation.png` and its JSON receipt. Pass when a domain configuration change does not alter another domain test configuration.
- [ ] Lane 8. Run `scripts/live-check.sh --case dg06-fresh-install`. Save `receipts/DG06/fresh-install.png` and its JSON receipt. Pass when a fresh checkout loads the plugin and completes the verified pilot.
- [ ] Lane 9. Run `scripts/live-check.sh --case dg06-upgrade-rollback`. Save `receipts/DG06/upgrade-rollback.png` and its JSON receipt. Pass when the documented upgrade and rollback preserve receipt history and configuration.
- [ ] Lane 10. Run `scripts/live-check.sh --case dg06-support-report`. Save `receipts/DG06/support-report.png` and its JSON receipt. Pass when every claimed supported domain has live evidence at the final head SHA.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Per-domain extraction and decision latency, install duration, memory, and cross-domain regression count.
- [ ] Probe. Run scripts/bench.sh --unit DG06 on the same app versions and task recordings at trunk and head. Compare each domain independently and keep missing-app results blocked.
- [ ] Baseline. Record trunk results first with hardware, app, model, concurrency, and input-size metadata. If trunk lacks the feature, record that fact and benchmark the added work directly.
- [ ] Rule. Before candidate tuning, freeze numeric absolute budgets and the allowed regression percentage in `eval-policy.json` using the initial baseline. Fail if a required budget is absent, a budget is exceeded, or a safety invariant fails. Require zero unauthorized, duplicate, and stale-state executions. Do not claim a ratio for unlike work.

**Review gate.** The operator reviews before merge.

- [ ] Present a screenshot of the real result and a short video for the changed interaction. Link the exact head SHA and required receipts. Keep operator merge approval separate from model acceptance.

**Merge.**

- [ ] Obtain an independent review where available. Reconcile the exact PR head with its verification ledger. Present any unavailable review as a limitation. The operator alone merges or promotes this unit.

## Close the program

- [ ] Reconcile every worker to a terminal state. Derive counts from the task ledger rather than narrative memory.
- [ ] Verify each public repository write contains only intended public material. Verify private data remained in its designated storage.
- [ ] Report all six PR URLs, branch names, head SHAs, checks, blocked domains, and actual measured cost from the private ledger.
- [ ] Deliver the plugin package, local launch instructions, evaluation report, and rollback procedure from the verified heads.
- [ ] Stop at merge-ready. Do not claim the complete program passed while any required live or performance check remains blocked.

## Appendix A. Prototype evidence

No GPU, application, plugin installation, or model-quality prototype ran during plan preparation. These questions remain unproven until the named units run locally.

- DG01 must establish the actual application seam and active local source branches. A README is not proof of an installed service.
- DG02 must verify plugin loading and available tools in both the local app and ChatGPT Work. A manifest alone is not an installed plugin.
- DG03 must establish Clef custom-head support on the actual ARM64 system. Existing ordinary Qwen support does not prove Clef support.
- DG04 must prove state freshness and execution authorization through a real application.
- DG05 must establish model quality on the owner's actual task distribution. Published generic benchmarks do not prove task-specific quality.
- DG06 must produce separate evidence for every claimed domain. The complete seven-domain target is not a claim of current support.

## Appendix B. Alternatives rejected

- Training a new 41.9M encoder first has no baseline advantage established. Keep it as a later compression proposal.
- Adding seven learned heads before evaluating question-conditioned models increases work without evidence of need.
- Letting a classifier invent repairs changes the intended bounded-output contract. Keep repair generation in the existing agent.
- Rebuilding all forks or copying all repository contents together makes ownership and upgrades harder. Inventory broadly and clone selectively.
- Copying Cursor Task calls or slash loops into Work does not implement those capabilities. Use explicit host adapters.
- Using micrograd as the action grader confuses automatic differentiation with correctness labels. Keep those responsibilities separate.
- Calling autoresearch an app grader confuses its optimization loop with the required task-specific correctness checks.

## Appendix C. Risks

- DG01 must distinguish source discovery from verified execution and preserve dirty local worktrees.
- DG02 must not rely on cloud Work plugin hooks. Confirm remote MCP reachability and authentication without exposing a general-purpose executor.
- DG03 must pin backend versions and validate probability semantics. Clef and generic SGLang decisions have different model paths and scheduling behavior.
- DG04 must prevent time-of-check to time-of-use errors. A model's accept verdict cannot bypass permissions or state checks.
- DG05 must prevent evaluation leakage, grader edits, and tuning against the final holdout. A process exit code is not task correctness.
- DG06 may encounter unavailable app installations. Record those limits per domain and continue independent adapters.
- The numeric budget, provider balance, model IDs, and private integration paths belong in local configuration. A provider name does not establish shared billing or transferable credits.
- Every live check requires a control tool or equivalent actual interface. If that capability is absent, retain the scenario and mark it blocked.

## Appendix D. Links and reading list

Use these sources as starting points. Resolve their current revisions before implementation and record those revisions in the inventory.

- [Owner's PStack fork](https://github.com/egc365/plugins/tree/99743e9c151c8537cbbf1f98bb38f34ef3368453/pstack). Version 0.15.25 at the planning snapshot.
- [PStack planning playbook](https://github.com/egc365/plugins/blob/99743e9c151c8537cbbf1f98bb38f34ef3368453/pstack/skills/poteto-mode/playbooks/multi-phase-plan.md).
- [PStack local Orchestrate playbook](https://github.com/egc365/plugins/blob/99743e9c151c8537cbbf1f98bb38f34ef3368453/pstack/skills/poteto-mode/playbooks/orchestrate.md). The separate Cursor SDK orchestrate plugin has different runtime requirements.
- Read `pstack/skills/how/SKILL.md` for DG01, DG02, and DG03 design decisions. Use `pstack/skills/interrogate/SKILL.md` when reviewers dispute a design. Keep the trail through `pstack/skills/show-me-your-work/SKILL.md`.
- [Karpathy micrograd](https://github.com/karpathy/micrograd/tree/7bc720e951fe422b8f8814aa5aa1b64121d26b4c). Upstream commit verified. No owner fork was found among accessible repositories during planning; fork/reuse remains an implementation task.
- [Existing autoresearch fork](https://github.com/egc365/autoresearch). Its verified upstream is `karpathy/autoresearch`. Adapt its loop only after the evaluator exists.
- [Existing Spark serving fork](https://github.com/egc365/Qwen3.8-27B-SGLang-DGX-Spark). Its verified upstream is `MiaAI-Lab/Qwen3.8-27B-SGLang-DGX-Spark`.
- [Jev reference collection](https://github.com/egc365/awesome-jev-by-typesafe).
- Inspect the existing public integration candidates [deepseek-harness](https://github.com/egc365/deepseek-harness), [dsh-codex-connect](https://github.com/egc365/dsh-codex-connect), and [dsh-xai](https://github.com/egc365/dsh-xai). Repository existence does not establish which checkout the owner currently uses.
- Inspect [sgl-cookbook](https://github.com/egc365/sgl-cookbook), [dgx-spark-playbooks](https://github.com/egc365/dgx-spark-playbooks), and [ms-swift](https://github.com/egc365/ms-swift) only for relevant serving or later training work.
- [Clef model card](https://huggingface.co/Cloudflare/clef) and [Clef Flash model card](https://huggingface.co/Cloudflare/clef-flash).
- [SGLang Clef cookbook](https://docs.sglang.io/cookbook/autoregressive/Cloudflare/clef). Clef uses `/v1/systemone` with its joint schema head.
- [SGLang decision models](https://docs.sglang.io/docs/supported-models/decision_models). Ordinary compatible chat models use `/v1/decisions` with answer-label probabilities.
- [TypeSafe introduction](https://docs.typesafe.ai/introduction) for Noul, Choice, and Score.
- [Build plugins](https://learn.chatgpt.com/docs/build-plugins) and [plugin runtime capabilities](https://learn.chatgpt.com/docs/plugins). Check supported host features before porting.

## Appendix E. Check the plan itself

Run `node pstack/skills/poteto-mode/scripts/check-plan.mjs plans/decision-gate/BUILD-PLAN.md` from the plugin checkout. This checks plan structure and wording. A passing plan check is not evidence that implementation tests or model evaluations passed.

The host adaptation intentionally changes PStack's default ten-cloud-VM procedure into ten scenarios with bounded concurrency. The user's existing authorization replaces an additional start prompt. Human-only merge, training, and promotion remain explicit. Missing tools do not become simulated successful checks.

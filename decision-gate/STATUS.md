# Program status & your three questions (2026-10-27 17:3x EDT)

## 1. The verification skill / auto-merge authority
What exists: gates/decision-gate-gates.md + executor (3 guards) + evaluator
(label-rev'd) + gate A/B harness. What it does: any agent action passes
permission->freshness->idempotency BEFORE execution, and task-completion is
judged from resulting state, not exit codes. That IS the verification layer;
'auto-merge' = it can be pointed at PR checks next (CI-read + verdict
posting), which is unbuilt and the natural DG02 tail.

Merge authority: YOURS per gates file. The machine verifies and recommends;
only you merge. When the verification layer covers the PR checks to your
standard, you can delegate the mechanical merge back to it - your call, one
sentence.

## 2. Memory: what's resident, what's freed, what's touchable
Freed this session: 3.4GB pip cache + trainer's 9GB on clean exit => 24-29GB
free (was 7 at the scare).
Resident now (deliberate):
- clef-flash serving ~21GB CPU+GPU (sglang, :30000) - the decision brain
- trace app + capture proxy + transcripts: <1GB total
- nanochat caches 2.6GB disk (not RAM)
Untouchable (other services): parakeet/MinerU hf caches ~8GB disk.
Levers if you need RAM: stop clef-sglang2 => ~20GB back, 3min restart cost.
GPU: free except sglang's idle residency.

## 3. Distance to the blender-bot
Built tonight: 30 REAL executed (goal,scene,recipe) pairs; retrieval layer
scores 100% on known-style phrasing (instance-LOO), 0% on unseen phrasings
(task-LOO) - that gap IS the remaining work, and it is data, not architecture:
(a) phrasing augmentation: 10-50 paraphrases per task => fixes task-LOO; days
(b) d8 text-LM prompt stage on the checkpoint (exists, hashed) => better
    ranking than ngrams; ~1 GPU-day
(c) the classifier head (42M, sized) for accept/reject on top: after (a)
Realistic: v0 blender-bot that executes correct commands on phrasings it has
seen: 1-2 sessions. General phrasing robustness: ~a week of accrual+retrain.
The fleet thesis holds: tiny, verified, narrow - then widen.

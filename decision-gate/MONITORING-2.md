# Training-watch ledger (round: fork discovery)

## Forked bot-training sessions FOUND (children of ef045a0e, the dead parent)
- b03520df 'Implement private data-prep module ONLY' - 31 steps, 54 tool calls, edits heavy, ACTIVE
- c6df1053 'Implement private training runner ONLY' - 30 steps, 75 tool calls, ACTIVE
- Both in Ground/Sketch todo phase; zero dg-worktree path overlap (no collision with our lineage)
- Their transcripts = reasoning-trace corpus on completion (the capture pattern from 438e1232 applies)

## Soul/6.1 bot-training status
- NOT visible from this box's user scope; owner runs it elsewhere
- Watch items when surfaces appear: loss curve, checkpoint writes, eval deltas vs the
  82.5% ngram bar, and the frozen criteria C1-C3 from gate_ab
- The gate harness here evaluates ANY checkpoint against the same frozen rules -
  bring the artifact, get the verdict

## Shady-behavior detector (owner directive)
- The ab.py false-accept/false-reject counts + the v1-blob/v3-good contrast pairs
  = the labeled signal. New Soul outputs get the same classification; regressions
  vs the 82.5%/gate criteria = 'shady', recorded as contrast pairs.

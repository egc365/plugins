# Watch list (owner directive 2026-10-27 evening)

1. Soul/6.1 training job (external infra, location unspecified by owner)
   - watch: loss trajectory, checkpoint writes, crash-restarts
   - risk named by owner: 'it likes to ruin everything' => verify each
     checkpoint against the task eval BEFORE it overwrites anything shared
   - local hook: when its checkpoints/outputs appear on shared disks, the
     gate A/B harness evaluates them against the same frozen criteria

2. d8 800-step: COMPLETE, both checkpoints hash-gated locally
   400=3895a039... 800=a2510355...

3. blender corpus: 121 rows incl the v1-blob/v3-good contrast pair
   (owner verdict encoded as labels - the discriminator trains on this)

4. next training gate: phrasing scale + task variety THEN SFT, owner sign-off
   per gates/decision-gate-gates.md. NO weights move before that.

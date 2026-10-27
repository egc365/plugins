# Memory runbook (owner heads-up 2026-10-27 ~18:00 EDT)

State now: ~22GB free / 121. Swap 11/15 used - keep eye on it.

## Safe shutdown order (biggest first, all restartable)
1. clef-sglang2 (clef-flash 9.4B resident, ~20GB CPU+GPU):
   systemctl --user stop clef-sglang2
   - restart: systemd-run --user --unit=clef-sglang2 ... (see history) or
     ask the agent; ~3min from disk, weights on /models NOT in tmp
2. clef-serve shim (8765, ~1GB): ALREADY STOPPED just now (redundant vs sglang)
3. transcript viewer 8801 (~100MB): systemctl --user stop claude-transcripts
4. trace app 8877 (~300MB): keep - it's the evidence store; cheap

## Do NOT stop
- claude-capture-proxy 8799: the training-data firehose, 50MB
- global-agent-traceability 8877: evidence store for everything above
- dsh/DeepSea, GLM containers, the owner's own jobs

## Disk (1.4T free - not the constraint)
- clef-flash weights 18G /models (keep; reload source)
- nanochat caches 2.6G (keep: pretok cache saves 20min/run)
- pip caches now purged (3.4G reclaimed earlier)

## Rule of thumb
Two model residencies max at once. d8 training run alone = 9GB GPU.
clef serving = ~20GB. Both together + desktop = the 13GB squeeze seen.
Pick one heavy resident at a time when other jobs run.

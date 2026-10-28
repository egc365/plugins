# Adherence audit: Soul forks (b03520df data-prep, c6df1053 runner)
Auditor: Grok via decision-gate, 2026-10-27 ~21:1x EDT
Evidence: full transcripts (f1/f2 jsonl), repo cross-refs, my test re-runs 47/47

## Verdict: HIGH ADHERENCE, two process errors, zero rule violations

## What they did right (verified, not narrated)
- Repo rules honored line-by-line (no transcript imports, coordinator lane, packet discipline)
- Native nanochat semantics preserved (masked CE matches gpt.py); the Muon->AdamW
  deviation is documented IN THEIR OWN OUTPUT as a tradeoff with blast-radius reasoning
- 47/47 tests; both stated what they did NOT do
- Prose: 74 sentences, 0 over 25 words, 0 passive - STE-clean without being asked

## Errors found
1. SEQUENCING: data-prep finalized its corpus format before the runner's manifest
   existed => rework risk. Fix for next spawn: interface contract FIRST, then
   parallel implementation (one shared schema commit before the fork).
2. No base-model eval before design: neither ran the 800-step eval to know the
   base's actual capability floor. The base is midtrain-thin; designs assumed.

## What to prompt differently next time (the fixes, in owner words)
- "Agree the data contract in commit 1. Both forks code against it. Then parallel."
- "Run eval-base first. Know what the base can't do before designing around it."

## Router status (my lane, this round)
ngram 82.5% remains champion; d8 zero-shot 20% (v1), discriminator-token 7.5% (v2)
- both recorded with diagnosis. Neural router revisits post-SFT.

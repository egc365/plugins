# Owner handoff: skills pinned, program state, no re-derivation

## Posted skills (verbatim copies in skills-input/)
- architect-SKILL.md    - sketch types/signatures/module structure BEFORE code
- statechart-SKILL.md   - TLA+ model -> Mermaid chart; bugs = numbered paths
- figure-it-out-SKILL.md - bespoke playbook when no narrow one fits

Owner directive: use these for the blender-bot program. Apply in order:
1. figure-it-out frames the whole program (done informally; formalize)
2. architect the data model + module seams (partially done: contracts/, adapters/)
3. statechart the blender job lifecycle BEFORE more training (NOT done - next)

## Where the program stands (evidence in git log + receipts/)
- contracts, executor(3 guards), evaluator(label-rev'd), clients(clef+sglang) - built, tested
- 6/7 domains live; blender adapter + failure corpus (79 rows: 27 gold)
- d8 base trained 400 steps + resume 400->800 IN FLIGHT (nanochat-d8-resume)
- dataset: 325 rows real + 30 blender pairs; gate arc v1 FAIL->v2 PASS
- 20 PRs open; operator merges only; $0 spent

## Hard rules from owner, this session
- NO human chat page; 8770 is bot-only JSON
- owner corrections = training curriculum (disposal ledger = gold labels)
- both sides of the coin: back-end bpy/API AND front-end visual/computer-use
- param counts must be measured, not invented (accessibility census pending)
- NO training past baseline until data ready + owner sign-off (gates file)

## Immediate next (this is the ordered queue)
1. statechart blender job lifecycle (from-chart; reader=owner; bugs=numbered)
2. front-side visual/computer-use feature census (measured param count)
3. phrasing augmentation to fix task-LOO 0.0 -> then re-run gate ab
4. team brief w/ statechart PNG + corpus stats; owner sign-off; then SFT

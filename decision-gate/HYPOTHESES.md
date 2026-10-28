# Harness-effect hypotheses (owner Q: why does it work better here?)

## H1: Autonomy preset (acceptEdits/no-interactive-gates)
Forks ran continuable+approval-policy preset, zero interactive pauses.
The chat environment has turn-by-turn. => fewer context switches, longer
unbroken execution blocks. TESTABLE: same task, same model, toggle preset.

## H2: Fresh context vs 40-turn parent
Forks started clean with a compact brief. Parent chat carries 100+ turns.
TESTABLE: run the same tasks in a fresh session vs this one.

## H3: Artifact-dense cwd
dg-worktree + decision-gate contracts + examples in the working dir gave the
model concrete anchors. TESTABLE: same task, empty cwd vs artifact-rich.

## H4: Identity confusion (fork believes it's the parent)
DISPROVEN by evidence: subagent/descriptor records show explicit
agentProvider=openai-codex, agentModel=gpt-6.1-sol, parent link to ef045a0e.
The forks knew exactly what they were.

## The honest answer
Two runs, two models, no controlled variable. ANY of H1-H3 could be the
needle-mover; none is proven. The test design above is how we find out -
one variable per run, same eval, N=5 tasks, compare gate pass-rates.
